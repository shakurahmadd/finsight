import numpy as np
from agent.tools import analyze_sentiment, get_news, get_sec_filings
from datetime import datetime, date, timedelta
from db.database import SessionLocal
from db.models import Watchlist, SentimentHistory, NewsArticle, AnomalyFeatures
import yfinance as yf
from edgar import Company
from sqlalchemy import func
from rag.filing_rag import process_filing


def fetch_and_cache_news():
    db = SessionLocal()
    try: 
        watchlist_tickers = db.query(Watchlist).all()
        for ticker in watchlist_tickers:
            try:
                articles = get_news.invoke(ticker.ticker)
                if not articles:
                    continue
                titles = [article['title'] for article in articles]
                sentiments = analyze_sentiment.invoke({"titles" : titles})
                for article, sentiment in zip(articles, sentiments):
                    if not article.get('description'):
                        continue
                    else:
                        news_article_row = NewsArticle(ticker = ticker.ticker,
                                                    title=article['title'],
                                                    content=article['description'], 
                                                    sentiment_label = sentiment['label'], 
                                                    sentiment_confidence = sentiment['confidence'])
                        db.add(news_article_row)
                db.commit()
            except Exception as e:
                print(f"Error for {ticker.ticker}: {e}")   
                db.rollback()
                continue             
    finally:
        db.close()
    score_and_store_sentiment()

    


def score_and_store_sentiment():
    db = SessionLocal()
    label_map = {'Bearish' : -1, 'Bullish' : 1, 'Neutral' : 0}
    try:
        watchlist_tickers = db.query(Watchlist).all()
        for ticker in watchlist_tickers:
            try:
                numerator = 0
                denominator = 0
                ticker_articles = db.query(NewsArticle).filter(NewsArticle.ticker == ticker.ticker).\
                    filter(NewsArticle.timestamp >= datetime.now() - timedelta(days=7)).all()
                

                article_titles = [article.title for article in ticker_articles]
                sentiment = analyze_sentiment.invoke({'titles' : article_titles})

                for sent, article in zip(sentiment, ticker_articles):
                    if not article.timestamp:
                        continue
                    else:
                        days_old = (date.today() - article.timestamp.date()).days
                        weight = sent['confidence'] * np.exp(-0.5 * days_old)
                        numerator += label_map[sent['label']] * weight
                        denominator += weight
                if denominator == 0:
                    continue
                else:
                    weighted_average = numerator / denominator
                    
                    sentiment_row = SentimentHistory(ticker = ticker.ticker, sentiment_score = float(weighted_average))
                    db.add(sentiment_row)
                    db.commit()
            except Exception as e:
                print(f"Error for {ticker.ticker}: {e}")
                db.rollback()
                continue
    finally:
        db.close()
    build_feature_vectors()



def build_feature_vectors():
    db = SessionLocal()
    try:
        watch_list_tickers = db.query(Watchlist).all()

        for row in watch_list_tickers:
            try:
                sentiment_row = db.query(SentimentHistory).filter(SentimentHistory.ticker == row.ticker)\
                    .filter(func.date(SentimentHistory.date) == date.today()).first()
                if sentiment_row == None:
                    continue

                ticker_obj = yf.Ticker(row.ticker)
                ticker_history = ticker_obj.history(period='30d')
                closing_price = ticker_history['Close']
                daily_returns = closing_price.pct_change()
                price_volatility = daily_returns.std()

                ticker_earnings_history = ticker_obj.earnings_history
                suprise_earnings = (ticker_earnings_history.iloc[0]['epsActual'] - ticker_earnings_history.iloc[0]['epsEstimate']) / np.abs(ticker_earnings_history.iloc[0]['epsEstimate']) * 100 

                sec_filings = get_sec_filings.invoke(row.ticker)
                form_4 = sec_filings['insider_traders']
                if isinstance(form_4, list):
                    insider_volume = 0
                    for shares in form_4:
                        insider_volume += shares['Shares']
                else:
                    insider_volume = 0
                c = Company(row.ticker)
                cutoff = (datetime.today() - timedelta(days=30)).strftime("%Y-%m-%d")
                ten_k = c.get_filings(form='10-K').filter(date= f"{cutoff}:")
                eight_k = c.get_filings(form='8-K').filter(date= f"{cutoff}:")
                form_four = c.get_filings(form='4').filter(date= f"{cutoff}:")
                
                filing_frequency = len(ten_k) + len(eight_k) + len(form_four)

                anomaly_features_row = AnomalyFeatures(ticker = row.ticker, date = datetime.today(), 
                                                       sentiment_score = sentiment_row.sentiment_score,
                                                       earnings_surprise = float(suprise_earnings),
                                                       insider_volume = insider_volume,
                                                       filing_frequency = filing_frequency,
                                                       price_volatility = float(price_volatility))
                
                db.add(anomaly_features_row)
                db.commit()

            except Exception as e:
                print(f"Error for {row.ticker}: {e}")
                db.rollback()
                continue


    finally:
        db.close()
    process_all_filings()



def process_all_filings():
    db = SessionLocal()
    try:
        watch_list_rows = db.query(Watchlist).all()
        for watch_list_row in watch_list_rows:
            process_filing(watch_list_row.ticker)

    finally:
        db.close()

    