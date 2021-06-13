import time
import typing
from datetime import datetime
from urllib.parse import urljoin

import bs4
import pymongo
import requests

from database.database import Database


class GbBlogParse:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0"
    }

    __parse_time = 0

    def __init__(self, start_url, db: Database, delay=1.0):
        self.start_url = start_url
        self.db = db
        self.delay = delay
        self.done_urls = set()
        self.tasks = []
        self.tasks_creator(
            {
                self.start_url,
            },
            self.parse_feed,
        )

    def _get_response(self, url):
        while True:
            next_time = self.__parse_time + self.delay
            if next_time > time.time():
                time.sleep(next_time - time.time())
            response = requests.get(url, headers=self.headers)
            print(f"RESPONSE: {response.url}")
            self.__parse_times = time.time()
            if response.status_code == 200:
                return response

    def get_task(self, url: str, callback: typing.Callable) -> typing.Callable:
        def task():
            response = self._get_response(url)
            return callback(response)

        return task

    def tasks_creator(self, urls: set, callback: typing.Callable):
        urls_set = urls - self.done_urls
        for url in urls_set:
            self.tasks.append(self.get_task(url, callback))
            self.done_urls.add(url)

    def run(self):
        while True:
            try:
                task = self.tasks.pop(0)
                task()
            except IndexError:
                break

    def parse_feed(self, response: requests.Response):
        soup = bs4.BeautifulSoup(response.text, "lxml")
        ul_pagination = soup.find("ul", attrs={"class": "gb__pagination"})
        pagination_links = set(
            urljoin(response.url, itm.attrs.get("href"))
            for itm in ul_pagination.find_all("a")
            if itm.attrs.get("href")
        )
        self.tasks_creator(pagination_links, self.parse_feed)
        post_wrapper = soup.find("div", attrs={"class": "post-items-wrapper"})
        self.tasks_creator(
            set(
                urljoin(response.url, itm.attrs.get("href"))
                for itm in post_wrapper.find_all(
                    "a", attrs={"class": "post-item__title"}
                )
                if itm.attrs.get("href")
            ),
            self.parse_post,
        )

    def _parse_first_image(self, soup: bs4.BeautifulSoup) -> str:
        return soup.find("img").attrs["src"]

    def _parse_datetime(self, soup: bs4.BeautifulSoup) -> datetime:
        return datetime.fromisoformat(
            soup.find("time", attrs={"itemprop": "datePublished"}).attrs[
                "datetime"
            ]
        )

    def _parse_comment(
        self, full_comment: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, str]:
        return {
            "id": full_comment["id"],
            "comment_author_url": full_comment["user"]["url"],
            "body": full_comment["body"],
        }

    def _parse_comments(
        self, soup: bs4.BeautifulSoup, url: str
    ) -> typing.List[typing.Dict[str, str]]:
        commentable_id = soup.find("comments").attrs.get("commentable-id")
        api_path = f"/api/v2/comments?commentable_type=Post&commentable_id={commentable_id}&order=desc"
        response = self._get_response(urljoin(url, api_path))
        return [
            self._parse_comment(comment["comment"])
            for comment in response.json()
        ]

    def parse_post(self, response: requests.Response):
        soup = bs4.BeautifulSoup(response.text, "lxml")
        author_name_tag = soup.find("div", attrs={"itemprop": "author"})
        data = {
            "post_data": {
                "title": soup.find("h1", attrs={"class": "blogpost-title"}).text,
                "url": response.url,
                'id': int(soup.find("comments").attrs.get("commentable-id")),
            },
            "author_data": {
                "url": urljoin(
                    response.url, author_name_tag.parent.attrs["href"]
                ),
                "name": author_name_tag.text,
            },
            "tags_data": [
                {"name": tag.text, "url": urljoin(response.url, tag.attrs.get("href"))} for tag in soup.find_all("a", attrs={"class": "small"})],
            "header_image": self._parse_first_image(soup),
            "published": self._parse_datetime(soup),
            "comments_data": self._parse_comments(soup, response.url),
        }
        self._save(data)

    def _save(self, data: dict):
        self.db.add_post(data)


if __name__ == "__main__":
    orm_database = Database("sqlite:///gb_blog_parse.db")
    parser = GbBlogParse("https://gb.ru/posts", orm_database)
    parser.run()