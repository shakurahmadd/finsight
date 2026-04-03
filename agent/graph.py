from typing import TypedDict
from pandas import DataFrame
from agent.tools import get_news, get_stock_data, analyze_sentiment
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph

load_dotenv()

groq_key = os.getenv("GROQ_API")
llm = ChatGroq(model="llama-3.1-8b-instant", api_key=groq_key)


class AgentState(TypedDict):
    ticker: str
    news: list[dict]
    stock_data: DataFrame
    sentiment: list[dict]
    summary: str


def get_news_node(state):
    # read from state
    ticker = state['ticker']
    # get news function
    articles = get_news(ticker)
    # return updated fields
    return {'news' : articles}


def get_stock_data_node(state):
    ticker = state['ticker']
    stock_data = get_stock_data(ticker)
    return {'stock_data' : stock_data}


def analyze_sentiment_node(state):
    articles = state['news']
    sentiment_labels = analyze_sentiment(articles)
    return {'sentiment' : sentiment_labels}


def generate_summaray_node(state):
    ticker = state['ticker']
    articles = state['news']
    stock_data = state['stock_data']
    sentiment = state['sentiment']
    prompt = f"""Act as a finace stock expert. You need to build a stock summary on the ticker: {ticker}. 
                To build you summary using the following article titles:          
                {articles}.
                The following stock data: 
                \n\n {stock_data}. 
                The following sentiment scores for the articles:
                {sentiment}"""
    response = llm.invoke(prompt)
    return {'summary' : response.content}



graph = StateGraph(AgentState)

graph.add_node("get_news", get_news_node)
graph.add_node("get_stock_data", get_stock_data_node)
graph.add_node("analyze_sentiment", analyze_sentiment_node)
graph.add_node("generate_summary", generate_summaray_node)

graph.set_entry_point("get_news")
graph.add_edge("get_news", "get_stock_data")
graph.add_edge("get_stock_data", "analyze_sentiment")
graph.add_edge("analyze_sentiment", "generate_summary")

# compile graph
graph_app = graph.compile()

if __name__ == "__main__":
    result = graph_app.invoke({"ticker" : "AAPL"})
    print(result['summary'])