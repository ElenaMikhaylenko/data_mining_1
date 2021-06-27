from typing import Callable, Optional, Tuple, List

from scrapy.loader import ItemLoader
from itemloaders.processors import MapCompose, TakeFirst, Join


TRASH_TEXTS = ("\x0a", "  ")


def have_information(value: str) -> Optional[str]:
    return value if value.replace(",", "").replace(" ", "") else None


def delete_trash_text(
    trash_texts: Tuple = TRASH_TEXTS,
) -> Callable[[str], str]:
    def inner(value: str) -> str:
        for text in trash_texts:
            value = value.replace(text, "")
        return value.strip()

    return inner


def make_name(values: List[str]) -> str:
    return " ".join(
        MapCompose(
            str.lower, delete_trash_text(), have_information, str.strip
        )(values)
    ).strip()


def make_text(values: List[str]) -> str:
    return "\n".join(MapCompose(delete_trash_text())(values))


make_lists = MapCompose(
    str.lower, str.strip, delete_trash_text(), have_information
)


def make_company_direction_out(values: List[str]) -> str:
    all_values = []
    for value in values:
        all_values.extend(value.split(","))
    return make_lists(all_values)


class HHVacancyLoader(ItemLoader):
    default_item_class = dict

    type_out = TakeFirst()
    title_out = TakeFirst()
    salary_out = Join("")
    vacancy_experience_out = TakeFirst()
    employment_out = make_lists
    description_out = make_text
    tag_list_out = make_lists
    author_url_out = TakeFirst()


class HHAuthorLoader(ItemLoader):
    default_item_class = dict

    type_out = TakeFirst()
    name_out = make_name
    description_out = make_text
    site_out = TakeFirst()
    company_directions_out = make_company_direction_out
