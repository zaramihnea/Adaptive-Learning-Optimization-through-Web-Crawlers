import hashlib
from sqlalchemy.exc import IntegrityError
from db.session import SessionLocal
from db.models import Document


class DeduplicationPipeline:
    def process_item(self, item, spider):
        text = (item.get("body") or "").encode("utf-8")
        item["content_hash"] = hashlib.sha256(text).hexdigest()
        return item


class PostgresPipeline:
    def open_spider(self, spider):
        self.session = SessionLocal()

    def close_spider(self, spider):
        self.session.close()

    def process_item(self, item, spider):
        existing = (
            self.session.query(Document)
            .filter_by(content_hash=item["content_hash"])
            .first()
        )
        if existing:
            spider.logger.debug(f"Duplicate skipped: {item['url']}")
            spider.crawler_stats["duplicate"] += 1
            return item

        doc = Document(
            url=item["url"],
            domain=item["domain"],
            title=item.get("title"),
            body=item.get("body"),
            language=item.get("language"),
            word_count=item.get("word_count", 0),
            content_hash=item["content_hash"],
            crawl_topic=item.get("crawl_topic"),
            learner_level=item.get("learner_level"),
        )
        try:
            self.session.add(doc)
            self.session.commit()
        except IntegrityError:
            # url unique constraint — already crawled via different path
            self.session.rollback()
            spider.crawler_stats["duplicate"] += 1

        return item
