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


load_dotenv()
news_api = os.getenv("NEWS_API")

set_identity("Shakur Ahmad shakurahmadd@gmail.com")

base_model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=3)
peft_model = PeftModel.from_pretrained(base_model, "shakurahmad/finsight-distilbert")
tokenizer = AutoTokenizer.from_pretrained("shakurahmad/finsight-distilbert")


@tool
def get_news(ticker: str):
    """
    Takes in user ticker and finds top 
    10 articles about the stock
    Args:
        ticker
    Returns:
        Articles as list of dictionaries
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
    Takes ticker value and collects relevant stock data from yfinance
    Args:
        ticker
    Returns:
        dictionary with stock history and fundamentals
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
    Takes a list of article title strings and returns sentiment labels.
    Args:
        titles: list of article title strings
    Returns:
        list of dicts with title and sentiment label
    """
    encoded_titles = tokenizer(titles, padding=True, truncation=True, max_length=128, return_tensors='pt')
    attention_mask = encoded_titles['attention_mask']
    input_ids = encoded_titles['input_ids']
    peft_model.eval()
    with torch.no_grad():
        output = peft_model(input_ids=input_ids, attention_mask=attention_mask)
        predicted_labels = torch.argmax(output.logits, dim=1)
        label_mapping = {0 : 'Bearish', 1 : 'Bullish', 2 : 'Neutral'}
        title_labels = []
        for index in predicted_labels:
            title_labels.append(label_mapping[index.item()])
        title_sentiment = [{'title' : title, 'label': label} for title, label in zip(titles, title_labels)]
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



