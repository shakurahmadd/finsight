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

load_dotenv()
news_api = os.getenv("NEWS_API")

base_model = AutoModelForSequenceClassification.from_pretrained("distilbert-base-uncased", num_labels=3)
peft_model = PeftModel.from_pretrained(base_model, "shakurahmad/finsight-distilbert")
tokenizer = AutoTokenizer.from_pretrained("shakurahmad/finsight-distilbert")


@tool
def get_news(ticker):
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
def get_stock_data(ticker):
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
    stock_data = {"history": historical_data, "fundamentals" : fundamentals}

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


    


