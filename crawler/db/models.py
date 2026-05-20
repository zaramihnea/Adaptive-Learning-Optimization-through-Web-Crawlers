from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, Index
from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(2048), unique=True, nullable=False)
    domain = Column(String(256), nullable=False)
    title = Column(String(1024))
    body = Column(Text)
    language = Column(String(16))
    crawled_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    content_hash = Column(String(64), index=True)  # SHA-256 for dedup
    word_count = Column(Integer)
    is_duplicate = Column(Boolean, default=False)

    # set at crawl time
    crawl_topic = Column(String(256))
    learner_level = Column(String(32))

    # filled later by ML pipeline
    topic_label = Column(String(128))
    difficulty = Column(String(32))
    relevance_score = Column(Float)

    __table_args__ = (
        Index("ix_documents_domain", "domain"),
        Index("ix_documents_topic", "topic_label"),
    )


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime)
    seed_url = Column(String(2048))
    topic = Column(String(256))
    learner_level = Column(String(32))   # beginner | intermediate | advanced
    learner_goal = Column(String(512))
    pages_crawled = Column(Integer, default=0)
    pages_skipped = Column(Integer, default=0)
    pages_duplicate = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    status = Column(String(32), default="running")  # running | done | failed
