from datetime import datetime
from pytz import timezone
from requests import Session
from bs4 import BeautifulSoup
from flask import abort
from dataclasses import asdict
from enum import Enum, auto

from json_feed_data import JsonFeedTopLevel, JsonFeedItem

MONEY_CNN_URL = 'https://money.cnn.com'
FGI_URI = '/data/fear-and-greed/'
FGI_FAVICON_URI = '/favicon.ico'
CNN_TZ = timezone('US/Eastern')

session = Session()


class ROUND(Enum):
    DAY = auto()
    HOUR = auto()


def extract_datetime(text, default_tz):
    datetime_formats = [
        'Last updated %b %d at %I:%M%p'
    ]

    # default timestamp
    datetime_obj = datetime.now()

    for datetime_format in datetime_formats:
        try:
            datetime_obj = datetime.strptime(text, datetime_format)
        except ValueError:
            pass

    # assume same year as query time, in US/Eastern timezone
    datetime_obj = datetime_obj.replace(
        year=datetime.now().astimezone(CNN_TZ).year)

    return datetime_obj.astimezone(timezone('UTC'))


# modified from https://stackoverflow.com/a/24893252
def remove_empty_from_dict(d):
    if isinstance(d, dict):
        return dict((k, remove_empty_from_dict(v)) for k, v in d.items() if v and remove_empty_from_dict(v))
    elif isinstance(d, list):
        return [remove_empty_from_dict(v) for v in d if v and remove_empty_from_dict(v)]
    else:
        return d


def get_latest_fgi(logger):
    page_url = MONEY_CNN_URL + FGI_URI

    logger.debug(f'Querying endpoint: {page_url}')
    page_response = session.get(page_url)

    # return HTTP error code
    if not page_response.ok:
        logger.debug('Error from source, dumping input:')
        logger.debug(page_response.text)
        abort(
            500, description=f"HTTP status from source: {page_response.status_code}")

    page_soup = BeautifulSoup(page_response.text, features='html.parser')
    feed_title = page_soup.title.text if page_soup else None

    json_feed = JsonFeedTopLevel(
        items=[],
        title=feed_title,
        home_page_url=page_url,
        favicon=MONEY_CNN_URL + FGI_FAVICON_URI
    )

    chart_section = page_soup.select_one('div#needleChart')

    if chart_section:
        fgi_values = chart_section.select('ul > li')
        fgi_value = next(iter(fgi_values), None)

        date_section = page_soup.select_one('div#needleAsOfDate')

        fgi_datetime = extract_datetime(date_section.text, CNN_TZ).isoformat(
            'T') if date_section else None

        feed_item = JsonFeedItem(
            id=fgi_datetime,  # use timestamp as unique id
            url=page_url,
            title=f"Fear & Greed Index - {date_section.text}",
            date_published=fgi_datetime,
            content_text=fgi_value.text
        )

        json_feed.items.append(feed_item)

    else:
        logger.warning('Chart section not found')

    return remove_empty_from_dict(asdict(json_feed))
