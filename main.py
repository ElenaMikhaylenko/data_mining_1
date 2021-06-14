import pymongo
from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from gb_parse.spiders.autoyoula import AutoyoulaSpider

if __name__ == "__main__":
    crawler_settings = Settings()
    crawler_settings.setmodule("gb_parse.settings")
    crawler_process = CrawlerProcess(settings=crawler_settings)
    db_client = pymongo.MongoClient("mongodb://localhost:27017")
    collection = db_client["data_mining_1"]["cars_info"]

    crawler_process.crawl(
        AutoyoulaSpider, save_callback=lambda data: collection.insert_one(data)
    )
    crawler_process.start()
