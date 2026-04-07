from sqlalchemy import Column, Integer, String, Text, DateTime
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


