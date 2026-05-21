"""Runs a single crawl in a fresh process — called by the API via subprocess."""
import os
import sys
import json
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "crawler.settings")

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from db.session import SessionLocal, init_db
from db.models import CrawlRun, CrawlRunDocument


def main():
    args = json.loads(sys.argv[1])
    run_id = args["run_id"]
    seed_urls = args["seed_urls"]
    topic = args["topic"]
    learner_level = args["learner_level"]
    depth = args["depth"]
    language = args.get("language", "en")

    init_db()

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(
        "edu",
        run_id=run_id,
        seed_urls=seed_urls,
        topic=topic,
        learner_level=learner_level,
        depth=depth,
        language=language,
    )
    process.start()

    session = SessionLocal()
    pages_crawled = session.query(CrawlRunDocument).filter_by(crawl_run_id=run_id).count()
    run = session.get(CrawlRun, run_id)
    run.finished_at = datetime.now(timezone.utc)
    run.status = "done"
    run.pages_crawled = pages_crawled
    session.commit()
    session.close()


if __name__ == "__main__":
    main()
