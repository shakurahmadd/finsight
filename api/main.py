from fastapi import FastAPI, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, ConfigDict
from agent.graph import graph_app
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import AnalysisResult, Watchlist, SentimentHistory, User
from sqlalchemy.exc import IntegrityError
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager
from api.jobs import fetch_and_cache_news
from api.auth import hash_password, verify_password, create_token, decode_token, get_current_user



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
   


scheduler = BackgroundScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # runs once when app starts
    scheduler.start()
    scheduler.add_job(fetch_and_cache_news, 'cron', hour=1, minute=0)

    yield # app is live here

    # runs once when app stops
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)

# Add analyse endpoint with pipe to LangGraph
@app.post("/analyse", response_model=AnalyseResponse)
def analyse(request: AnalyseRequest, db: Session = Depends(get_db)):
    check = db.query(AnalysisResult).filter_by(ticker=request.ticker).first()
   
    if check is None:
        result = graph_app.invoke({'ticker' : request.ticker})
        new_result = AnalysisResult(ticker=request.ticker, summary=result['summary'])
        db.add(new_result)
        db.commit()
        return AnalyseResponse(ticker=request.ticker, summary=result['summary'], timestamp=datetime.now(timezone.utc)) 
    
    elif (datetime.now(timezone.utc) - check.timestamp) > timedelta(days=1):
        result = graph_app.invoke({'ticker' : request.ticker})
        check.summary = result['summary']
        check.timestamp = datetime.now(timezone.utc)
        db.commit()
        return AnalyseResponse(ticker=request.ticker, summary=result['summary'], timestamp=datetime.now(timezone.utc))
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
   


