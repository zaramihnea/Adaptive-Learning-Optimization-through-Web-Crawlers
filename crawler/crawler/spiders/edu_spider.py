from urllib.parse import urlparse
import scrapy
import trafilatura
from crawler.items import DocumentItem

BLOCKED_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "linkedin.com", "tiktok.com", "youtube.com", "reddit.com",
}


class EduSpider(scrapy.Spider):
    name = "edu"

    custom_settings = {}

    def __init__(self, seed_urls=None, topic="", learner_level="beginner", depth=2, run_id=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = seed_urls or []
        self.topic = topic.lower().strip()
        self.learner_level = learner_level
        self.run_id = run_id
        self.topic_keywords = set(self.topic.replace(",", " ").split())
        self.custom_settings["DEPTH_LIMIT"] = int(depth)
        self.crawler_stats = {"crawled": 0, "duplicate": 0, "skipped": 0, "errors": 0}

    def parse(self, response):
        if response.status != 200:
            self.crawler_stats["errors"] += 1
            return

        extracted = trafilatura.extract(
            response.text,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_recall=True,
        )

        if not extracted or len(extracted.split()) < 50:
            self.crawler_stats["skipped"] += 1
        else:
            domain = urlparse(response.url).netloc
            title = response.css("title::text").get(default="").strip()

            yield DocumentItem(
                url=response.url,
                domain=domain,
                title=title,
                body=extracted,
                language=self._detect_language(extracted),
                word_count=len(extracted.split()),
                crawl_run_id=self.run_id,
            )
            self.crawler_stats["crawled"] += 1

        for href, anchor_text in self._extract_links(response):
            url = response.urljoin(href)
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                continue
            if any(blocked in parsed.netloc for blocked in BLOCKED_DOMAINS):
                continue
            if self._is_topic_relevant(parsed.path, anchor_text):
                yield scrapy.Request(url, callback=self.parse)

    def _is_topic_relevant(self, path: str, anchor_text: str) -> bool:
        if not self.topic_keywords:
            return True
        combined = (path + " " + anchor_text).lower()
        return any(kw in combined for kw in self.topic_keywords)

    def _extract_links(self, response):
        for a in response.css("a"):
            href = a.attrib.get("href", "")
            anchor = a.css("::text").get(default="")
            if href:
                yield href, anchor

    def _detect_language(self, text: str) -> str:
        try:
            import langdetect
            return langdetect.detect(text)
        except Exception:
            return "en"

    def closed(self, reason):
        self.logger.info(
            f"Crawl finished — reason={reason} stats={self.crawler_stats}"
        )
