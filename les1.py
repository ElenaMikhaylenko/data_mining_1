import json
import time
from typing import *
from pathlib import Path
import requests


class Parse5ka:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:87.0) "
        "Gecko/20100101 Firefox/87.0"
    }

    def __init__(self, start_url, save_path: Path):
        self.start_url = start_url
        self.save_path = save_path

    def _get_response(self, url):
        while True:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response
            time.sleep(0.5)

    def run(self):
        for product in self._parse(self.start_url):
            file_path = self.save_path.joinpath(f"{product['id']}.json")
            self._save(product, file_path)

    def _parse(self, url):
        while url:
            response = self._get_response(url)
            data: dict = response.json()
            url = data["next"]
            for product in data["results"]:
                yield product

    def _save(self, data: dict, file_path: Path):
        file_path.write_text(json.dumps(data, ensure_ascii=False))


class Categories5ka(Parse5ka):
    def __init__(self, categories_url: str, *args, **kwargs):
        self.categories_url = categories_url
        super().__init__(*args, **kwargs)

    def get_categories(self) -> List[Dict]:
        return self._get_response(self.categories_url).json()

    def run(self):
        for cat in self.get_categories():
            result_cat = {
                "name": cat["parent_group_name"],
                "code": cat["parent_group_code"],
                "products": list(
                    self._parse(
                        "https://5ka.ru/api/v2/special_offers/?categories="
                        + cat["parent_group_code"]
                    )
                ),
            }
            print(result_cat)
            self._save(
                result_cat,
                self.save_path.joinpath(
                    (
                        f"{cat['parent_group_code']}_{cat['parent_group_name']}.json"
                    )
                ),
            )


def get_save_path(dir_name: str) -> Path:
    save_path = Path(__file__).parent.joinpath(dir_name)
    if not save_path.exists():
        save_path.mkdir()
    return save_path


if __name__ == "__main__":
    url = "https://5ka.ru/api/v2/special_offers/"
    url_cat = "https://5ka.ru/api/v2/categories/"
    product_path = get_save_path("products")
    parser = Parse5ka(url, product_path)
    parser_cat = Categories5ka(url_cat, url, product_path)
    # parser.run()
    parser_cat.run()
