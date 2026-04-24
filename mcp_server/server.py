from agent.tools import analyze_sentiment, get_stock_data, get_news, retrieve_rag_chunks, get_earnings
from mcp.server.fastmcp import FastMCP

# create the server
mcp = FastMCP("finsight", host="0.0.0.0", port=8001)


@mcp.tool()
def get_news_tool(ticker: str):
    """
    Use this tool to get the latest news articles for a specific ticker.
    Args:
        ticker: company ticker as a string
    Returns:
        list of article dicts, each containing 'title', 'description', 'publishedAt', and 'url'
    """
    return get_news(ticker)


@mcp.tool()
def get_stock_data_tool(ticker: str):
    """
    Use this tool to find numerical data about a ticker. This includes historical data and stock fundementals
    Args:
        ticker
    Returns:
        dictionary with stock history and fundamentals including marketCap, trailingPE, sector, and company name
    """    
    return get_stock_data(ticker)


@mcp.tool()
def analyze_sentiment_tool(titles: list[str]) -> list[dict]:
    """
    Use this tool to compute sentiment on news article headlines.
    Call get_news first and extract the 'title' field from each article,
    then pass the list of titles here.
    Args:
        titles: list of headline strings extracted from get_news results
    Returns:
        list of dicts with 'title', 'label' (Bullish/Bearish/Neutral), and 'confidence' score
    """
    return analyze_sentiment(titles)


@mcp.tool()
def retrieve_rag_chunks_tool(query : str, ticker : str):
    """
    Retrieve relevant SEC filing chunks for a given ticker and query.                                                                                         
    Use this tool when you need information about risk factors, management discussion,                                                                        
    or material events (8-K) from SEC filings. Returns the most relevant sections
    based on the query.  
    Args:
        query: a specific question or topic to retrieve, e.g. "liquidity risk" or "revenue concentration"
        ticker: the company ticker, used to scope the search to that company's filings
    """
    return retrieve_rag_chunks(query, ticker)



@mcp.tool()
def get_earnings_tool(ticker: str):
    """
    Use this tool to retrieve historical EPS (earnings per share) data for a ticker.
    Returns actual vs estimated EPS and the surprise percentage for each quarter.
    Use this to assess whether management guidance is credible and whether the company
    has a pattern of beating or missing estimates.
    Args:
        ticker: company ticker as a string
    Returns:
        list of dicts, each containing:
        - 'date': the earnings date
        - 'eps_actual': reported EPS for that quarter
        - 'eps_estimate': analyst consensus estimate
        - 'surprise': percentage by which actual beat or missed estimate 
                      (positive = beat, negative = miss)
    """
    return get_earnings(ticker)


if __name__ == "__main__":
    mcp.run(transport="sse")

