import numpy as np
from agent.tools import analyze_sentiment, get_news
from datetime import datetime, date, timedelta
from db.database import SessionLocal
from db.models import Watchlist, SentimentHistory, NewsArticle


def fetch_and_cache_news():
    db = SessionLocal()
    try: 
        watchlist_tickers = db.query(Watchlist).all()
        for ticker in watchlist_tickers:
            try:
                articles = get_news.invoke(ticker.ticker)

                for article in articles:
                    if not article.get('description'):
                        continue
                    else:
                        news_article_row = NewsArticle(ticker = ticker.ticker,
                                                    title=article['title'],
                                                    content=article['description'])
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

