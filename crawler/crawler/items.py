import scrapy


class DocumentItem(scrapy.Item):
    url = scrapy.Field()
    domain = scrapy.Field()
    title = scrapy.Field()
    body = scrapy.Field()
    language = scrapy.Field()
    word_count = scrapy.Field()
    content_hash = scrapy.Field()
    crawl_run_id = scrapy.Field()
    crawl_topic = scrapy.Field()
    learner_level = scrapy.Field()
