from typing import TypedDict
from pandas import DataFrame

class AgentState(TypedDict):
    ticker: str
    news: list[dict]
    stock_data: DataFrame
    sentiment: list[dict]
    summary: str

