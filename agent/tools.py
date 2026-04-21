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
    newsapi = NewsApiClient(api_key=news_api)
    all_articles = newsapi.get_everything(q=ticker,
                                      language='en',
                                      from_param= (datetime.today() - timedelta(days=7)),
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
    historical_data = historical_data.drop(columns=['Open', 'Stock Splits'])

    info = ticker_obj.info
    fundamentals = {'marketCap' : info['marketCap'], 
                    'trailingPE': info['trailingPE'], 
                    'sector' : info['sector'], 
                    'longName' : info['longName']}
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
        title_sentiment = [{'title' : title, 'label': label, 'confidence' : conf.item()} for title, label, conf in zip(titles, title_labels, confidence)]
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
    ten_k = c.get_filings(form='10-K').latest().obj()

    try:
        eight_k = c.get_filings(form='8-K').latest().obj()
    except:
        eight_k = None
        print(f'8K form missing for {c}')

    try:
        form_4 = c.get_filings(form='4').latest().obj()
    except:
        form_4 = None
        print(f'4K form missing for {c}')
 

    sec_dict = {
        'management_discussion' : ten_k.management_discussion[:3000],
        'risk_factors' : ten_k.risk_factors[:3000],
        'eight_k': eight_k.text()[:3000] if eight_k else "No recent 8-K found",
        'insider_traders' : form_4.market_trades.to_dict(orient='records') if form_4 else "No recent Form 4 found"
    }
    return sec_dict


@tool
def retrieve_rag_chunks(query : str, ticker : str, top_k : int = 5):
    """
    Retrieve relevant SEC filing chunks for a given ticker and query.                                                                                         
    Use this tool when you need information about risk factors, management discussion,                                                                        
    or material events (8-K) from SEC filings. Returns the most relevant sections
    based on the query.  
    Args:
        query: a specific question or topic to retrieve, e.g. "liquidity risk" or "revenue concentration"
        ticker: the company ticker, used to scope the search to that company's filings
        top_k: number of chunks to return (default 5)
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
    eps_actuals = ticker_history['epsActual']
    eps_estimates = ticker_history['epsEstimate']
    dates = ticker_history.index
    surprises = ((eps_actuals - eps_estimates) / abs(eps_estimates) * 100 )
    return [{'date' : str(date), 'eps_actual' : eps_actual, 'eps_estimate' : eps_estimate, 'surprise' : surprise}
             for date, eps_actual, eps_estimate, surprise in zip(dates, eps_actuals, eps_estimates, surprises)] 