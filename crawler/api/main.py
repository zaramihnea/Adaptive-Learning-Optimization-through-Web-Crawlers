import os
import sys
import json
import logging
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "crawler.settings")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone

from db.session import SessionLocal, init_db
from db.models import CrawlRun, CrawlRunDocument, Document

logger = logging.getLogger(__name__)

app = FastAPI(title="EduCrawl API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type"],
)


@app.on_event("startup")
def startup():
    init_db()


# ── schemas ───────────────────────────────────────────────────────────────────

class CrawlRequest(BaseModel):
    seed_urls: list[str]
    topic: str
    learner_level: str = "beginner"
    learner_goal: Optional[str] = None
    depth: int = 2


class RecommendationItem(BaseModel):
    id: int
    url: str
    domain: str
    title: Optional[str]
    preview: Optional[str]
    language: Optional[str]
    word_count: Optional[int]
    difficulty: Optional[str]
    topic_label: Optional[str]
    relevance_score: Optional[float]


class CrawlResponse(BaseModel):
    run_id: int
    topic: str
    learner_level: str
    learner_goal: Optional[str]
    pages_crawled: int
    recommendations: list[RecommendationItem]


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.post("/crawl", response_model=CrawlResponse)
def crawl(req: CrawlRequest):
    """
    Crawl + return results when done.
    Blocks until crawl finishes then returns all collected documents.
    """
    session = SessionLocal()
    run = CrawlRun(
        started_at=datetime.now(timezone.utc),
        seed_url=", ".join(req.seed_urls),
        topic=req.topic,
        learner_level=req.learner_level,
        learner_goal=req.learner_goal,
        status="running",
    )
    session.add(run)
    session.commit()
    run_id = run.id
    session.close()

    try:
        crawler_dir = os.path.join(os.path.dirname(__file__), "..")
        python = sys.executable
        run_crawler = os.path.join(crawler_dir, "run_crawl.py")
        args = json.dumps({
            "run_id": run_id,
            "seed_urls": req.seed_urls,
            "topic": req.topic,
            "learner_level": req.learner_level,
            "depth": req.depth,
        })
        result = subprocess.run(
            [python, run_crawler, args],
            cwd=crawler_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
    except Exception:
        logger.exception(f"Crawl failed for run_id={run_id}")
        session = SessionLocal()
        run = session.get(CrawlRun, run_id)
        run.status = "failed"
        run.finished_at = datetime.now(timezone.utc)
        session.commit()
        session.close()
        raise HTTPException(status_code=500, detail="Crawl failed")

    session = SessionLocal()
    pages_crawled = session.query(CrawlRunDocument).filter_by(crawl_run_id=run_id).count()
    run = session.get(CrawlRun, run_id)
    run.finished_at = datetime.now(timezone.utc)
    run.status = "done"
    run.pages_crawled = pages_crawled
    session.commit()

    recommendations = _get_recommendations(session, run_id)
    result = CrawlResponse(
        run_id=run_id,
        topic=run.topic or "",
        learner_level=run.learner_level or "",
        learner_goal=run.learner_goal,
        pages_crawled=pages_crawled,
        recommendations=recommendations,
    )
    session.close()
    return result


@app.get("/crawl", response_model=CrawlResponse)
def get_results(
    topic: str,
    learner_level: str = "beginner",
    learner_goal: Optional[str] = None,
    seed_url: Optional[str] = None,
):
    """
    Fetch results from DB for a previous crawl matching the given profile.
    Returns the most recent matching run.
    """
    session = SessionLocal()
    query = (
        session.query(CrawlRun)
        .filter(CrawlRun.topic == topic, CrawlRun.learner_level == learner_level, CrawlRun.status == "done")
    )
    if learner_goal:
        query = query.filter(CrawlRun.learner_goal == learner_goal)
    if seed_url:
        query = query.filter(CrawlRun.seed_url.ilike(f"%{seed_url}%"))

    run = query.order_by(CrawlRun.started_at.desc()).first()
    if not run:
        session.close()
        raise HTTPException(status_code=404, detail="No results found for this profile. Try POST /crawl first.")

    recommendations = _get_recommendations(session, run.id)
    result = CrawlResponse(
        run_id=run.id,
        topic=run.topic or "",
        learner_level=run.learner_level or "",
        learner_goal=run.learner_goal,
        pages_crawled=run.pages_crawled or 0,
        recommendations=recommendations,
    )
    session.close()
    return result


# ── NLP endpoints ─────────────────────────────────────────────────────────────

@app.get("/documents/unclassified")
def get_unclassified(limit: int = 100):
    """NLP pipeline: fetch documents that haven't been classified yet."""
    session = SessionLocal()
    docs = session.query(Document).filter(Document.difficulty == None).limit(limit).all()
    result = [{"id": d.id, "title": d.title, "body": d.body, "word_count": d.word_count} for d in docs]
    session.close()
    return result


@app.patch("/documents/{doc_id}")
def classify_document(doc_id: int, difficulty: Optional[str] = None, topic_label: Optional[str] = None):
    """NLP pipeline: write back difficulty + topic_label."""
    session = SessionLocal()
    doc = session.get(Document, doc_id)
    if not doc:
        session.close()
        raise HTTPException(status_code=404, detail="Document not found")
    if difficulty:
        doc.difficulty = difficulty
    if topic_label:
        doc.topic_label = topic_label
    session.commit()
    session.close()
    return {"ok": True}


@app.patch("/runs/{run_id}/documents/{doc_id}/score")
def set_relevance_score(run_id: int, doc_id: int, relevance_score: float):
    """NLP pipeline: write relevance score for a document within a run."""
    session = SessionLocal()
    rd = session.query(CrawlRunDocument).filter_by(crawl_run_id=run_id, document_id=doc_id).first()
    if not rd:
        session.close()
        raise HTTPException(status_code=404, detail="Document not in this run")
    rd.relevance_score = relevance_score
    session.commit()
    session.close()
    return {"ok": True}


# ── helper ────────────────────────────────────────────────────────────────────

def _get_recommendations(session, run_id: int) -> list[RecommendationItem]:
    rows = (
        session.query(CrawlRunDocument, Document)
        .join(Document, CrawlRunDocument.document_id == Document.id)
        .filter(CrawlRunDocument.crawl_run_id == run_id)
        .order_by(CrawlRunDocument.relevance_score.desc().nullslast())
        .all()
    )
    return [
        RecommendationItem(
            id=doc.id,
            url=doc.url,
            domain=doc.domain,
            title=doc.title,
            preview=(doc.body or "")[:400] or None,
            language=doc.language,
            word_count=doc.word_count,
            difficulty=doc.difficulty,
            topic_label=doc.topic_label,
            relevance_score=rd.relevance_score,
        )
        for rd, doc in rows
    ]
