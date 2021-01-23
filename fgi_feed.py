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
        year=CNN_TZ.localize(datetime.now()).year)

    return CNN_TZ.localize(datetime_obj)


# modified from https://stackoverflow.com/a/24893252
def remove_empty_from_dict(d):
    if isinstance(d, dict):
        return dict((k, remove_empty_from_dict(v)) for k, v in d.items() if v and remove_empty_from_dict(v))
    elif isinstance(d, list):
        return [remove_empty_from_dict(v) for v in d if v and remove_empty_from_dict(v)]
    else:
        return d


def get_latest_fgi(logger, method=None):
    url = MONEY_CNN_URL + FGI_URI

    logger.debug(f'Querying endpoint: {url}')
    try:
        response = session.get(url)
    except Exception as ex:
        logger.debug('Exception:' + ex)
        abort(500, description=ex)

    # return HTTP error code
    if not response.ok:
        logger.error('Error from source')
        logger.debug('Dumping input:' + response.text)
        abort(
            500, description='HTTP status from source: ' + str(response.status_code))

    page_soup = BeautifulSoup(response.text, features='html.parser')
    feed_title = page_soup.title.text if page_soup else None

    json_feed = JsonFeedTopLevel(
        items=[],
        title=feed_title,
        home_page_url=url,
        favicon=MONEY_CNN_URL + FGI_FAVICON_URI
    )

    chart_section = page_soup.select_one('div#needleChart')

    if chart_section:
        fgi_values = chart_section.select('ul > li')
        fgi_value = fgi_values[0]
        fgi_absolute_value = fgi_value.text.replace('Fear & Greed Now: ', '')
        fgi_close_value = fgi_values[1]

        date_section = page_soup.select_one('div#needleAsOfDate')

        fgi_datetime = extract_datetime(
            date_section.text, CNN_TZ) if date_section else None

        if method == ROUND.DAY:
            item_title = fgi_close_value.text
            item_date_published = fgi_datetime.replace(minute=0, hour=0)
            item_content_text = 'As of ' + fgi_datetime.strftime('%b %d')
        elif method == ROUND.HOUR:
            item_title = 'Fear & Greed Hourly: ' + fgi_absolute_value
            item_date_published = fgi_datetime.replace(minute=0)
            item_content_text = 'Since ' + \
                fgi_datetime.strftime('%b %d %I:00 %p')
        else:
            item_title = fgi_value.text
            item_date_published = fgi_datetime
            item_content_text = date_section.text

        item_date_published_formatted = item_date_published.isoformat('T')

        feed_item = JsonFeedItem(
            id=item_date_published_formatted,  # use timestamp as unique id
            url=url,
            title=item_title,
            date_published=item_date_published_formatted,
            content_text=item_content_text
        )

        json_feed.items.append(feed_item)

    else:
        logger.warning('Chart section not found')

    return remove_empty_from_dict(asdict(json_feed))
