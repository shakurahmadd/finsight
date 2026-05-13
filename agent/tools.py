from dotenv import load_dotenv
import requests
import os
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from peft import PeftModel
import torch
import yfinance as yf
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from langchain_core.tools import tool
from edgar import Company, set_identity
from rag.filing_rag import retrieve_chunks
from db.database import SessionLocal
from db.models import NewsArticle                                                                                                             


load_dotenv()
news_api = os.getenv("NEWS_API")

set_identity("Shakur Ahmad shakurahmadd@gmail.com")

base_model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=3)
peft_model = PeftModel.from_pretrained(base_model, "shakurahmad/finsight-distilbert")
tokenizer = AutoTokenizer.from_pretrained("shakurahmad/finsight-distilbert")


@tool
def get_news(ticker: str):
    """
    Use this tool to get the latest news articles for a specific ticker.
    Args:
        ticker: company ticker as a string
    Returns:
        list of article dicts, each containing 'title', 'description', 'publishedAt', and 'url'
    """
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(hours=24)
        cached = db.query(NewsArticle).filter(
            NewsArticle.ticker == ticker,
            NewsArticle.timestamp >= cutoff
        ).limit(10).all()
        if cached:
            return [{'title': a.title, 'description': a.content, 'publishedAt': str(a.timestamp), 'url': ''} for a in cached]
    finally:
        db.close()

    newsapi = NewsApiClient(api_key=news_api)
    all_articles = newsapi.get_everything(q=ticker,
                                          language='en',
                                          from_param=(datetime.today() - timedelta(days=7)),
                                          sort_by='relevancy',
                                          page_size=10)
    return all_articles['articles']


@tool
def get_stock_data(ticker: str):
    """
    Use this tool to find numerical data about a ticker. This includes historical data and stock fundementals
    Args:
        ticker
    Returns:
        dictionary with stock history and fundamentals including marketCap, trailingPE, sector, and company name
    """
    ticker_obj = yf.Ticker(ticker)
    historical_data = ticker_obj.history(start= (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d'), 
                                         end=datetime.today().strftime('%Y-%m-%d'))
    historical_data = historical_data.drop(columns=['Open', 'Stock Splits'], errors='ignore')
    info = ticker_obj.info
    raw_cap = info.get('marketCap')
    if raw_cap is None:
        market_cap = "N/A"
    elif raw_cap >= 1_000_000_000_000:
        market_cap = f"${raw_cap / 1_000_000_000_000:.1f}T"
    elif raw_cap >= 1_000_000_000:
        market_cap = f"${raw_cap / 1_000_000_000:.1f}B"
    else:
        market_cap = f"${raw_cap / 1_000_000:.1f}M"
    raw_pe = info.get('trailingPE')
    trailing_pe = round(raw_pe, 2) if raw_pe is not None else 'N/A'
    fundamentals = {'marketCap': market_cap,
                    'trailingPE': trailing_pe,
                    'sector': info.get('sector', 'N/A'),
                    'longName': info.get('longName', ticker)}
    stock_data = {"history": historical_data.to_dict(orient='records'), "fundamentals" : fundamentals}

    return stock_data

@tool  
def analyze_sentiment(titles: list[str]) -> list[dict]:
    """
    Use this tool to compute sentiment on news article headlines.
    Call get_news first and extract the 'title' field from each article,
    then pass the list of titles here.
    Args:
        titles: list of headline strings extracted from get_news results
    Returns:
        list of dicts with 'title', 'label' (Bullish/Bearish/Neutral), and 'confidence' score
    """
    encoded_titles = tokenizer(titles, padding=True, truncation=True, max_length=128, return_tensors='pt')
    attention_mask = encoded_titles['attention_mask']
    input_ids = encoded_titles['input_ids']
    peft_model.eval()
    with torch.no_grad():
        output = peft_model(input_ids=input_ids, attention_mask=attention_mask)
        predicted_labels = torch.argmax(output.logits, dim=1)
        probs = torch.softmax(output.logits, dim=1)
        confidence = torch.max(probs, dim=1).values
        label_mapping = {0 : 'Bearish', 1 : 'Bullish', 2 : 'Neutral'}
        title_labels = []
        for index in predicted_labels:
            title_labels.append(label_mapping[index.item()])
        title_sentiment = [{'title': title, 'label': label, 'confidence': round(conf.item(), 2)} for title, label, conf in zip(titles, title_labels, confidence)]
    return title_sentiment


    
@tool
def get_sec_filings(ticker: str):
    """
    Takes a company ticker and grabs its most recent 10-K, 8-K and Form 4
    Args:
        Ticker: company ticker as a string
    Returns: 
        A dictionary contining, management discussion and risk factors from the 10-K.
        The 8-K text and insider trading records from Form 4. 
    """
    c = Company(ticker)
    try:
        ten_k = c.get_filings(form='10-K').latest().obj()
    except Exception:
        ten_k = None
        print(f'10-K is missing for {c}')
    try:
        eight_k = c.get_filings(form='8-K').latest().obj()
    except Exception:
        eight_k = None
        print(f'8K form missing for {c}')

    try:
        form_4 = c.get_filings(form='4').latest().obj()
            
    except Exception:
        form_4 = None
        print(f'4K form missing for {c}')
 

    sec_dict = {
        'management_discussion' : ten_k.management_discussion[:3000] if ten_k else "No recent 10-K found",
        'risk_factors' : ten_k.risk_factors[:3000] if ten_k else "No recent 10-K found",
        'eight_k': eight_k.text()[:3000] if eight_k else "No recent 8-K found",
        'insider_traders' : form_4.market_trades.to_dict(orient='records') if form_4 and not form_4.market_trades.empty else "No recent Form 4 found"
    }
    return sec_dict


@tool
def retrieve_rag_chunks(query : str, ticker : str):
    """
    Retrieve relevant SEC filing chunks for a given ticker and query.                                                                                         
    Use this tool when you need information about risk factors, management discussion,                                                                        
    or material events (8-K) from SEC filings. Returns the most relevant sections
    based on the query.  
    Args:
        query: a specific question or topic to retrieve, e.g. "liquidity risk" or "revenue concentration"
        ticker: the company ticker, used to scope the search to that company's filings
    """
    top_k_chunks = retrieve_chunks(query, ticker)
    return [ {'section': top_k_chunk.section, 'text' : top_k_chunk.chunk_text[:300]} for top_k_chunk in top_k_chunks]




@tool
def get_earnings(ticker : str ):
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
    ticker_obj = yf.Ticker(ticker)
    ticker_history = ticker_obj.earnings_history
    if ticker_history is None or ticker_history.empty:
        return "No earnings data available"
    eps_actuals = ticker_history['epsActual']
    eps_estimates = ticker_history['epsEstimate']
    dates = ticker_history.index
    surprises = ((eps_actuals - eps_estimates) / abs(eps_estimates) * 100)
    return [{'date': str(date), 'eps_actual': round(float(eps_actual), 2), 'eps_estimate': round(float(eps_estimate), 2), 'surprise': round(float(surprise), 2)}
            for date, eps_actual, eps_estimate, surprise in zip(dates, eps_actuals, eps_estimates, surprises)]