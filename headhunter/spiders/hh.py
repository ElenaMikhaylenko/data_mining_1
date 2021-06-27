from typing import Generator, Optional, Union

import scrapy
from scrapy.item import Item
from scrapy.selector import SelectorList, Selector
from scrapy.http.response import Response, Request

from ..loaders import HHVacancyLoader, HHAuthorLoader


class UnknownVacancyError(Exception):
    ...


class HHMixin:

    _VACANCY_BASE_XPATH_PATTERN = "//div[contains(@data-qa, 'vacancy-serp__vacancy') and contains(@data-qa, '%s')]"
    _VACANCY_HREF_PATTERN = "//a[@data-qa='vacancy-serp__vacancy-title']/@href"

    VACANCIES_TYPES = {
        "standard": "vacancy-serp__vacancy_standard",
        "standard-plus": "vacancy-serp__vacancy_standard_plus",
        "premium": "vacancy-serp__vacancy_premium",
    }

    VACANCY_STRUCTURE = {
        "title": "//h1[@data-qa='vacancy-title']//text()",
        "salary": "//p[@class='vacancy-salary']//text()",
        "vacancy_experience": "//span[@data-qa='vacancy-experience']//text()",
        "employment": "//p[@data-qa='vacancy-view-employment-mode']//text()",
        "description": "//div[@data-qa='vacancy-description']//text()",
        "tag_list": "//div[@class='bloko-tag-list']//text()",
    }

    AUTHOR_URL = "//a[@class='vacancy-company-name']/@href"

    AUTHOR_STRUCTURE = {
        "name": "//div[@class='employer-sidebar-header']//span[@class='company-header-title-name']//text()",
        "description": "//div[@class='company-description']//text()",
        "site": "//a[@data-qa='sidebar-company-site']/@href",
        "company_directions": "//div[@class='bloko-text-emphasis']/../p//text()",
    }

    def get_vacancies_urls(
        self, response: Response, vacancy_type: str
    ) -> SelectorList:
        vacancy_xpath = self.VACANCIES_TYPES.get(vacancy_type)
        if vacancy_xpath is None:
            raise UnknownVacancyError(vacancy_xpath)
        return response.xpath(
            self._VACANCY_BASE_XPATH_PATTERN % vacancy_xpath
        ).xpath(self._VACANCY_HREF_PATTERN)

    def get_next_page_url(self, response: Response) -> Optional[Selector]:
        return response.xpath(
            "//span[@data-qa='pager-page']/../following::*[1]/a/@href"
        ).get()


class HHSpider(scrapy.Spider, HHMixin):
    name = "hh"
    allowed_domains = ["hh.ru"]
    start_urls = [
        "https://spb.hh.ru/search/vacancy?schedule=remote&L_profession_id=0&area=113"
    ]

    def __init__(self, *args, **kwargs):
        self.handled_vacancies = {
            "standard": self.parse_standard_vacancy,
            "standard-plus": self.parse_standard_vacancy,
            "premium": self.parse_premium_vacancy,
        }
        super().__init__(*args, **kwargs)

    def parse_author(self, response: Response) -> Generator[Item, None, None]:
        loader = HHAuthorLoader(response=response)
        for data_key, data_xpath in self.AUTHOR_STRUCTURE.items():
            loader.add_xpath(data_key, data_xpath)
        loader.add_value("type", "author")
        yield loader.load_item()

    def parse_standard_vacancy(
        self, response: Response
    ) -> Generator[Union[Request, Item], None, None]:
        loader = HHVacancyLoader(response=response)
        for data_key, data_xpath in self.VACANCY_STRUCTURE.items():
            loader.add_xpath(data_key, data_xpath)
        author_url = response.urljoin(response.xpath(self.AUTHOR_URL).get())
        loader.add_value("author_url", author_url)
        loader.add_value("type", "vacancy")
        yield loader.load_item()
        yield response.follow(author_url, callback=self.parse_author)

    def parse_premium_vacancy(self, response: Response) -> ...:
        # Sometimes we have special pages like work in McDonalds
        return self.parse_standard_vacancy(response)

    def parse(self, response: Response) -> Generator[Request, None, None]:
        for vacancy_type, vacancy_parser in self.handled_vacancies.items():
            yield from response.follow_all(
                self.get_vacancies_urls(response, vacancy_type),
                callback=vacancy_parser,
            )
        next_page = self.get_next_page_url(response)
        if next_page is None:
            return
        yield response.follow(next_page)
