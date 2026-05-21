import hashlib
from sqlalchemy.exc import IntegrityError
from db.session import SessionLocal
from db.models import Document, CrawlRunDocument


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
        run_id = item.get("crawl_run_id")

        # check if document already exists globally
        doc = self.session.query(Document).filter_by(url=item["url"]).first()

        if doc is None:
            doc = Document(
                url=item["url"],
                domain=item["domain"],
                title=item.get("title"),
                body=item.get("body"),
                language=item.get("language"),
                word_count=item.get("word_count", 0),
                content_hash=item["content_hash"],
            )
            try:
                self.session.add(doc)
                self.session.flush()  # get doc.id without committing
            except IntegrityError:
                self.session.rollback()
                doc = self.session.query(Document).filter_by(url=item["url"]).first()
                spider.crawler_stats["duplicate"] += 1

        # link document to this crawl run (skip if already linked)
        if run_id and doc:
            already_linked = (
                self.session.query(CrawlRunDocument)
                .filter_by(crawl_run_id=run_id, document_id=doc.id)
                .first()
            )
            if not already_linked:
                self.session.add(CrawlRunDocument(crawl_run_id=run_id, document_id=doc.id))

        try:
            self.session.commit()
        except IntegrityError:
            self.session.rollback()
            spider.crawler_stats["duplicate"] += 1

        return item
