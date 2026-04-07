from fastapi import FastAPI
from datetime import datetime
from pydantic import BaseModel
from agent.graph import graph_app


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
def analyse(request: AnalyseRequest):
    result = graph_app.invoke({'ticker' : request.ticker})
    return AnalyseResponse(ticker=request.ticker, summary=result['summary'], timestamp=datetime.today())


