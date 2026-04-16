from fastapi import FastAPI, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ConfigDict
from agent.graph import graph_app
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import AnalysisResult, Watchlist, SentimentHistory, User, Portfolio, Holdings, NewsArticle
from sqlalchemy.exc import IntegrityError
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from api.jobs import fetch_and_cache_news
from api.auth import hash_password, verify_password, create_token, decode_token, get_current_user
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage



# build pydantic models for request and response
class AnalyseRequest(BaseModel):
    ticker : str


class AnalyseResponse(BaseModel):
    ticker : str
    summary : str
    timestamp : datetime


class WatchlistRequest(BaseModel):
    ticker : str

class SentimentHistoryResponse(BaseModel):
    # tells Pydantic it can read attributes from a SQLAlchemy object directly
    model_config = ConfigDict(from_attributes=True)
    ticker : str
    date : datetime
    sentiment_score : float


class AuthRequest(BaseModel):
    email : str
    password : str
   
class PortfolioRequest(BaseModel):
    name : str


class HoldingRequest(BaseModel):
    ticker : str
    shares : float




scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs once when app starts
    scheduler.start()
    scheduler.add_job(fetch_and_cache_news, 'cron', hour=1, minute=0)

    yield # app is live here

    # runs once when app stops
    scheduler.shutdown()



# accept requests from react dev server
app = FastAPI(lifespan=lifespan)
app.add_middleware(                                                                                                                                       
      CORSMiddleware,                                                                                                                                       
      allow_origins=["http://localhost:5173"],                                                                                                            
      allow_methods=["*"],                    
      allow_headers=["*"],                
  )




# Add analyse endpoint with pipe to LangGraph
@app.post("/analyse", response_model=AnalyseResponse)
def analyse(request: AnalyseRequest, db: Session = Depends(get_db)):
    check = db.query(AnalysisResult).filter_by(ticker=request.ticker).first()
   
    if check is None:
        result = graph_app.invoke({'messages' : [HumanMessage(content = f"Provide and alaysis on the ticker: {request.ticker}")]})
        new_result = AnalysisResult(ticker=request.ticker, summary=result['messages'][-1].content)
        db.add(new_result)
        db.commit()
        return AnalyseResponse(ticker=request.ticker, summary=result['messages'][-1].content, timestamp=datetime.now(timezone.utc)) 
    
    elif (datetime.now(timezone.utc) - check.timestamp) > timedelta(days=1):
        result = graph_app.invoke({'messages' : [HumanMessage(content = f"Provide and alaysis on the ticker: {request.ticker}")]})
        check.summary = result['messages'][-1].content
        check.timestamp = datetime.now(timezone.utc)
        db.commit()
        return AnalyseResponse(ticker=request.ticker, summary=result['messages'][-1].content, timestamp=datetime.now(timezone.utc))
    else:
        return AnalyseResponse(ticker = request.ticker, summary=check.summary, timestamp=check.timestamp)
    

@app.get("/results/{ticker}")
def get_results(ticker: str, db: Session = Depends(get_db)):
    check = db.query(AnalysisResult).filter_by(ticker=ticker).first()
    if check is None:
        raise HTTPException(status_code=404, detail="No results found for this ticker")
    else:
        return AnalyseResponse(ticker = ticker, summary=check.summary, timestamp=check.timestamp)



@app.post("/watchlist", status_code=201)
def add_to_watchlist(request : WatchlistRequest, db : Session = Depends(get_db)):
    try:
        new_watchlist_item = Watchlist(ticker = request.ticker)
        db.add(new_watchlist_item)
        db.commit()
        return f"{request.ticker} has been added to the watchlist."
    except IntegrityError:
        db.rollback()
        # conflict
        raise HTTPException(status_code=409, detail=f"{request.ticker} is already in the watchlist.")


@app.delete("/watchlist/{ticker}")
def delete_from_wishlist(ticker: str, db: Session = Depends(get_db)):
    row = db.query(Watchlist).filter(Watchlist.ticker == ticker).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{ticker} is not in the watchlist.")
    else:
        db.delete(row)
        db.commit()
        return f"{ticker} removed from the watchlist."

    
@app.get("/sentiment/history/{ticker}", response_model=list[SentimentHistoryResponse])
def get_sentiment_history(ticker: str, db: Session = Depends(get_db)):
    cutoff = datetime.now() - timedelta(days=30)

    get_rows = db.query(SentimentHistory)\
        .filter(SentimentHistory.ticker == ticker)\
            .filter(SentimentHistory.date >= cutoff)\
                .order_by(SentimentHistory.date.asc())\
                .all()

    return get_rows


# Registration endpoint
@app.post("/register", status_code=201)
def register(request : AuthRequest, db : Session = Depends(get_db)):
    check_duplicates = db.query(User).filter(User.email == request.email).first()
    if check_duplicates == None:
        hash_pass = hash_password(request.password)
        input_user_info = User(email = request.email, hashed_password = hash_pass)
        db.add(input_user_info)
        db.commit()

        return "You have registered succesfully"
    else:
        raise HTTPException(status_code=409, detail='User already exsits')


# Login endpoint
@app.post("/login", status_code=200)
def login(request : AuthRequest, db : Session = Depends(get_db)):
    user_row = db.query(User).filter(User.email == request.email).first()
    if user_row == None:
        raise HTTPException(status_code=401, detail="User does not exist, please register.")
    check_pass = verify_password(request.password, user_row.hashed_password)
    if check_pass == False:
        raise HTTPException(status_code=401, detail='Login details are incorrect')
    else:
        user_token = create_token(user_row.id)
        return {'access_token' : user_token, 'token_type' : 'bearer'}
   


@app.post("/portfolio")
def create_postfolio(request : PortfolioRequest, db : Session = Depends(get_db), current_user = Depends(get_current_user)):
    user_port_rows = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).filter(Portfolio.name == request.name).first()
    if user_port_rows is None:
        portfolio_row = Portfolio(name = request.name, user_id = current_user.id)
        
        db.add(portfolio_row)
        db.commit()
        return {"id" : portfolio_row.id, "name" : portfolio_row.name}
    else:
        raise HTTPException(status_code=409, detail="Name already exists in your portfolio.")


@app.get("/portfolio")
def get_portfolio(db : Session = Depends(get_db), current_user = Depends(get_current_user)):
    portfolio_rows  = db.query(Portfolio).filter(Portfolio.user_id == current_user.id).all()
    return [{"id" : row.id, "name" : row.name} for row in portfolio_rows]
    

@app.delete("/portfolio/{portfolio_id}")
def delete_portfolio(portfolio_id : int, current_user = Depends(get_current_user), db : Session = Depends(get_db)):
    portfolio_row = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if portfolio_row == None:
        raise HTTPException(status_code=404, detail="Porfolio id does not exist")
    if portfolio_row.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have acess to this portfolio")
    else:
        db.delete(portfolio_row)
        db.commit()
        return f"{portfolio_row.name} has been deleted"
    

@app.post('/holdings/{portfolio_id}')
def add_holdings(portfolio_id : int, request : HoldingRequest, db : Session = Depends(get_db), current_user = Depends(get_current_user)):
    port_row = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if port_row is None:
        raise HTTPException(status_code = 404, detail="Porfolio does not exist")
    if port_row.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have acess to this portfolio")
    else:
        holdings_row = Holdings(portfolio_id = portfolio_id, ticker = request.ticker, shares = request.shares)
        db.add(holdings_row)
        db.commit()
        return {"id" : holdings_row.id, "ticker" : holdings_row.ticker, "shares" : holdings_row.shares}
    


@app.get('/holdings/{portfolio_id}')
def get_holdings(portfolio_id : int, db : Session = Depends(get_db), current_user = Depends(get_current_user)): 
    port_row = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if port_row == None:
        raise HTTPException(status_code=404, detail= "Holding does not exist")
    if port_row.user_id != current_user.id:
        raise HTTPException(status_code=403, detail= "You do not have acess to this holding")
    else:
        holding_row = db.query(Holdings).filter(Holdings.portfolio_id == portfolio_id).all()
        return [{"id" : row.id, "ticker" : row.ticker, "shares" : row.shares } for row in holding_row]
    

    
@app.delete('/holdings/{portfolio_id}/{holdings_id}')
def delete_holdings(portfolio_id : int, holdings_id : int, db : Session = Depends(get_db), current_user = Depends(get_current_user)):
    port_row = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if port_row == None:
        raise HTTPException(status_code=404, detail= "This portfolio does not exist")
    if port_row.user_id != current_user.id:
        raise HTTPException(status_code=403, detail = "You do not have acess to this holding")
    else:
        holdings_row = db.query(Holdings).filter(Holdings.id == holdings_id).first()
        if holdings_row == None:
            raise HTTPException(status_code=404, detail="This holding does not exist")
        else:
            db.delete(holdings_row)
            db.commit()
            return f"{holdings_id} has been deleted from portfolio: {portfolio_id}"



@app.get('/portfolio/{portfolio_id}/summary')
def get_portfolio_summary(portfolio_id : int, db : Session = Depends(get_db), current_user = Depends(get_current_user)):
    portfolio_row = db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
    if portfolio_row == None:
        raise HTTPException(status_code=404, detail="Portfolio does not exist")
    if portfolio_row.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You do not have acess to this portfolio")
    else:
        # weighted_sentiment = sum(sentiment_i * shares_i) / sum(shares_i for tickers with data)
        holdings = db.query(Holdings).filter(Holdings.portfolio_id == portfolio_id).all()
        tickers = [row.ticker for row in holdings]
        shares = [row.shares for row in holdings]
        numerator = 0
        denominator = 0
        for ticker, share in zip(tickers, shares):
            sentiment = db.query(SentimentHistory).filter(SentimentHistory.ticker == ticker).first()
            if sentiment is None:
                continue # skip both numerator and denominator
            else:
                numerator += (sentiment.sentiment_score * share) 
                denominator += share
        if denominator == 0:
            return "No sentiment data is available"
        else:
            portfolio_sentiment = numerator / denominator
            return portfolio_sentiment
        


@app.get('/news/{ticker}')
def get_news_ticker(ticker : str, db : Session = Depends(get_db)):
    news_article_rows = db.query(NewsArticle).filter(NewsArticle.ticker == ticker)\
        .order_by(NewsArticle.timestamp.desc()).limit(10).all()
    if not news_article_rows:
        raise HTTPException(status_code=404, detail="No articles exist")
    else:
        return [{"title" : row.title, "sentiment_label" : row.sentiment_label, 
                 "sentiment_confidence" : row.sentiment_confidence, 
                 "timestamp": row.timestamp} for row in news_article_rows]







    
