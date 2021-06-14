import re

import scrapy


class CarParserMixin:

    _authors_patterns = {
        "https://youla.ru/user": re.compile(
            r"youlaId%22%2C%22([A-Za-z0-9]+)%22%2C%22avatar"
        ),
        "https://auto.youla.ru/cardealers": re.compile(
            r"cardealers%2F([A-Za-z0-9\-]+)%2F%23info"
        ),
    }

    def _get_author_url_by_pattern(self, response, url, pattern) -> str:
        result = re.findall(pattern, response.text)
        if result:
            return f"{url}/{result[0]}"

    def _parse_one_characteristic(self, characteristic_selector):
        key = characteristic_selector.css(
            ".AdvertSpecs_label__2JHnS::text"
        ).extract_first()
        value = characteristic_selector.css(
            ".AdvertSpecs_data__xK2Qx::text"
        ).extract_first()
        if value is None:
            value = characteristic_selector.css(
                ".blackLink::text"
            ).extract_first()
        return key, value

    def _get_characteristics(self, response) -> dict:
        result = {}
        for characteristic in response.css(
            ".AdvertCard_specs__2FEHc .AdvertSpecs_row__ljPcX"
        ):
            key, value = self._parse_one_characteristic(characteristic)
            result[key] = value
        return result

    def _get_author_url(self, response):
        for url, pattern in self._authors_patterns.items():
            result = self._get_author_url_by_pattern(response, url, pattern)
            if result is not None:
                return result

    def _get_description(self, response):
        return response.css(
            ".AdvertCard_descriptionInner__KnuRi::text"
        ).extract_first()

    def _get_title(self, response):
        return response.css(
            ".AdvertCard_advertTitle__1S1Ak::text"
        ).extract_first()

    def _get_photos(self, response):
        result = []
        for photo_selector in response.css(
            ".PhotoGallery_photoWrapper__3m7yM .PhotoGallery_photo__36e_r .PhotoGallery_photoImage__2mHGn"
        ):
            result.append(photo_selector.attrib.get("src"))
        return result


class AutoyoulaSpider(scrapy.Spider, CarParserMixin):
    name = "autoyoula"
    allowed_domains = ["auto.youla.ru"]
    start_urls = ["https://auto.youla.ru/"]

    _css_selectors = {
        "brands": "div.ColumnItemList_container__5gTrc a.blackLink",
        "pagination": "div.Paginator_block__2XAPy a.Paginator_button__u1e7D",
        "car": ".SerpSnippet_titleWrapper__38bZM a.SerpSnippet_name__3F7Yu",
    }

    def __init__(self, save_callback, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._save = save_callback

    def _get_follow(self, response, css_selector, callback, **kwargs):
        for link_selector in response.css(css_selector):
            yield response.follow(
                link_selector.attrib.get("href"), callback=callback
            )

    def parse(self, response):
        yield from self._get_follow(
            response, self._css_selectors["brands"], self.brand_parse
        )

    def brand_parse(self, response):
        yield from self._get_follow(
            response, self._css_selectors["car"], self.car_parse
        )
        yield from self._get_follow(
            response, self._css_selectors["pagination"], self.brand_parse
        )

    def car_parse(self, response):
        data = {
            "title": self._get_title(response),
            "url": response.url,
            "description": self._get_description(response),
            "author": self._get_author_url(response),
            "characteristics": self._get_characteristics(response),
            "photos": self._get_photos(response),
        }

        self._save(data)
