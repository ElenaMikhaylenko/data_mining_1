from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from headhunter.spiders.hh import HHSpider


def main() -> None:
    crawler_settings = Settings()
    crawler_settings.setmodule("headhunter.settings")
    crawler_process = CrawlerProcess(settings=crawler_settings)
    crawler_process.crawl(HHSpider)
    # Add uk and etc
    crawler_process.start()


if __name__ == "__main__":
    main()
