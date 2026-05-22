import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "educrawl"
SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = float(os.getenv("CRAWL_DELAY", "1.5"))
RANDOMIZE_DOWNLOAD_DELAY = True

COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en",
    "User-Agent": "EduCrawl/1.0 (academic research crawler; contact: zaramihnea@gmail.com)",
}

ITEM_PIPELINES = {
    "crawler.pipelines.DeduplicationPipeline": 100,
    "crawler.pipelines.PostgresPipeline": 200,
}

# disable offsite blocking - we want cross-domain crawling
DOWNLOADER_MIDDLEWARES = {
    "scrapy.downloadermiddlewares.offsite.OffsiteMiddleware": None,
}

CLOSESPIDER_PAGECOUNT = int(os.getenv("MAX_PAGES", "500"))

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
