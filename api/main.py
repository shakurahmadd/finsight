from fastapi import FastAPI, Depends, HTTPException
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from agent.graph import graph_app
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import AnalysisResult


# build pydantic models for request and response
class AnalyseRequest(BaseModel):
    ticker : str



class AnalyseResponse(BaseModel):
    ticker : str
    summary : str
    timestamp : datetime


app = FastAPI()

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


        