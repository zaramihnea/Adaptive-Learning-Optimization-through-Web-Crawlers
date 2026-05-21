from sqlalchemy import Column, Integer, String, Text, DateTime, Float, UniqueConstraint, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
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
    content_hash = Column(String(64), index=True)
    word_count = Column(Integer)

    # filled by NLP pipeline — content-based, not profile-based
    topic_label = Column(String(128))
    difficulty = Column(String(32))  # beginner | intermediate | advanced

    runs = relationship("CrawlRunDocument", back_populates="document")

    __table_args__ = (
        Index("ix_documents_domain", "domain"),
    )


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime)
    seed_url = Column(String(2048))
    topic = Column(String(256))
    learner_level = Column(String(32))  # beginner | intermediate | advanced
    learner_goal = Column(String(512))
    pages_crawled = Column(Integer, default=0)
    pages_skipped = Column(Integer, default=0)
    pages_duplicate = Column(Integer, default=0)
    errors = Column(Integer, default=0)
    status = Column(String(32), default="running")

    documents = relationship("CrawlRunDocument", back_populates="run")


class CrawlRunDocument(Base):
    """Join table: links a document to a crawl run (learner profile)."""
    __tablename__ = "crawl_run_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crawl_run_id = Column(Integer, ForeignKey("crawl_runs.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    relevance_score = Column(Float)  # filled by NLP pipeline

    run = relationship("CrawlRun", back_populates="documents")
    document = relationship("Document", back_populates="runs")

    __table_args__ = (
        UniqueConstraint("crawl_run_id", "document_id", name="uq_run_document"),
    )
