from urllib.parse import urlparse, urlunparse
import scrapy
import trafilatura
from crawler.items import DocumentItem

BLOCKED_DOMAINS = {
    "facebook.com", "twitter.com", "x.com", "instagram.com",
    "linkedin.com", "tiktok.com", "youtube.com", "reddit.com",
}

NON_ENGLISH_PREFIXES = (
    "/zh-", "/ru/", "/ja/", "/fr/", "/de/", "/es/", "/pt-",
    "/ko/", "/ar/", "/it/", "/pl/", "/tr/", "/vi/", "/uk/",
)


class EduSpider(scrapy.Spider):
    name = "edu"

    custom_settings = {}

    def __init__(self, seed_urls=None, topic="", learner_level="beginner", depth=2, run_id=None, language="en", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = seed_urls or []
        self.topic = topic.lower().strip()
        self.learner_level = learner_level
        self.run_id = run_id
        self.language = language or "en"
        self.topic_keywords = set(self.topic.replace(",", " ").split())
        self.custom_settings["DEPTH_LIMIT"] = int(depth)
        self.crawler_stats = {"crawled": 0, "duplicate": 0, "skipped": 0, "errors": 0}

    def parse(self, response):
        if response.status != 200:
            self.crawler_stats["errors"] += 1
            return

        content_type = response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore").lower()
        if "text/html" not in content_type:
            self.crawler_stats["skipped"] += 1
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
            return

        lang = self._detect_language(extracted)
        if not self._is_target_language(lang):
            self.crawler_stats["skipped"] += 1
        else:
            domain = urlparse(response.url).netloc
            title = response.css("title::text").get(default="").strip()

            yield DocumentItem(
                url=response.url,
                domain=domain,
                title=title,
                body=extracted,
                language=lang,
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
            if parsed.path.lower().endswith((".zip", ".pdf", ".tar.gz", ".exe", ".dmg", ".png", ".jpg", ".gif", ".svg", ".mp4", ".mp3", ".ipynb")):
                continue
            target_prefix = f"/{self.language}/"
            if any(parsed.path.startswith(p) for p in NON_ENGLISH_PREFIXES) and not parsed.path.startswith(target_prefix):
                continue
            # normalize before following to avoid duplicate crawls
            url = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", "", ""))
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
            return self.language

    def _is_target_language(self, detected: str) -> bool:
        if self.language == "en":
            # langdetect is unreliable on technical content - be permissive for English
            return detected not in ("zh-cn", "zh-tw", "ru", "ja", "ko", "ar", "th", "fa")
        # for non-English targets, require an exact match
        return detected == self.language

    def closed(self, reason):
        self.logger.info(
            f"Crawl finished — reason={reason} stats={self.crawler_stats}"
        )
