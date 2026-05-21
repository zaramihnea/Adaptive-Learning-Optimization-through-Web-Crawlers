import os
import sys
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from db.session import init_db
from db.models import CrawlRun, CrawlRunDocument
from db.session import SessionLocal
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault("SCRAPY_SETTINGS_MODULE", "crawler.settings")

LEVELS = ("beginner", "intermediate", "advanced")


def prompt_inputs():
    print("\n=== EduCrawl ===")

    raw_urls = input("Seed URLs (comma-separated): ").strip()
    seed_urls = [u.strip() for u in raw_urls.split(",") if u.strip()]
    if not seed_urls:
        print("No URLs provided, exiting.")
        sys.exit(1)

    topic = input("Topic (e.g. machine learning, python basics): ").strip()

    level = input("Learner level [beginner / intermediate / advanced] (default: beginner): ").strip().lower()
    if level not in LEVELS:
        level = "beginner"

    goal = input("Learner goal (e.g. 'understand neural networks', optional): ").strip()

    raw_depth = input("Crawl depth (default 2): ").strip()
    depth = int(raw_depth) if raw_depth.isdigit() else 2

    return seed_urls, topic, level, goal, depth


def main():
    init_db()

    seed_urls, topic, learner_level, learner_goal, depth = prompt_inputs()

    print(f"\nStarting crawl")
    print(f"  Seeds:  {seed_urls}")
    print(f"  Topic:  {topic}")
    print(f"  Level:  {learner_level}")
    print(f"  Goal:   {learner_goal or '—'}")
    print(f"  Depth:  {depth}\n")

    session = SessionLocal()
    run = CrawlRun(
        started_at=datetime.now(timezone.utc),
        seed_url=", ".join(seed_urls),
        topic=topic,
        learner_level=learner_level,
        learner_goal=learner_goal or None,
    )
    session.add(run)
    session.commit()
    run_id = run.id

    settings = get_project_settings()
    process = CrawlerProcess(settings)
    process.crawl(
        "edu",
        run_id=run_id,
        seed_urls=seed_urls,
        topic=topic,
        learner_level=learner_level,
        depth=depth,
    )
    process.start()

    # update stats from actual DB counts after crawl finishes
    pages_crawled = session.query(CrawlRunDocument).filter_by(crawl_run_id=run_id).count()

    run = session.get(CrawlRun, run_id)
    run.finished_at = datetime.now(timezone.utc)
    run.status = "done"
    run.pages_crawled = pages_crawled
    session.commit()
    session.close()

    print(f"\nDone — {pages_crawled} documents collected.")


if __name__ == "__main__":
    main()
