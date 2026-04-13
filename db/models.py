from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean
from db.database import Base
from datetime import datetime, timezone

class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default = lambda: datetime.now(timezone.utc), nullable=False)


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True)
    ticker = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), default = lambda: datetime.now(timezone.utc), nullable=False)

class DkKnowledge(Base):
    __tablename__ = "dk_knowledge"

    id = Column(Integer, primary_key=True)
    sector = Column(String, nullable=False)
    metric_name = Column(String, nullable=False)
    sector_avg = Column(Float, nullable=False)
    std_dev = Column(Float, nullable=False)
    upper_threshold = Column(Float, nullable=False)
    lower_threshold = Column(Float, nullable=False)
    importance = Column(Float, nullable=False)

class MacroIndicator(Base):
    __tablename__ = 'macro_indicator'

    id = Column(Integer, primary_key=True)
    indicator_name = Column(String, nullable=False)
    current_value = Column(Float, nullable=False)
    change = Column(Float, nullable=False)
    time_stamp = Column(DateTime(timezone=True), default= lambda: datetime.now(timezone.utc), nullable=False)
    importance = Column(Float, nullable=False)


class SectorMacroMapping(Base):
    __tablename__ = 'sector_macro_map'

    sector = Column(String, primary_key=True)
    indicator_id = Column(Integer, primary_key=True)


class Watchlist(Base):
    __tablename__ = 'watch_list'

    ticker = Column(String, primary_key=True)


class SentimentHistory(Base):
    __tablename__ = 'sentiment_history'

    ticker = Column(String, primary_key=True)
    date = Column(DateTime(timezone=True), default= lambda: datetime.now(timezone.utc), primary_key=True)
    sentiment_score = Column(Float, nullable=False)
    

class AnomalyFeatures(Base):
    __tablename__ = 'anomaly_features'

    ticker = Column(String, primary_key=True)
    date = Column(DateTime(timezone=True), primary_key=True)
    sentiment_score = Column(Float, nullable=False)
    earnings_surprise = Column(Float, nullable=False)
    insider_volume = Column(Float, nullable=False)
    filing_frequency = Column(Float, nullable=False)
    price_volatility = Column(Float, nullable=False)
    anomaly_score = Column(Float, nullable=True)
    is_anomaly = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), default = lambda : datetime.now(timezone.utc), nullable=False)


