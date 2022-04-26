from datetime import datetime
from requests import Session
from flask import abort
from dataclasses import asdict
from enum import Enum, auto

from json_feed_data import JsonFeedTopLevel, JsonFeedItem

FGI_JSON_URL = 'https://production.dataviz.cnn.io'
FGI_JSON_URI = '/index/fearandgreed/graphdata'
CNN_URL = 'https://edition.cnn.com'
CNN_FAVICON_URI = '/media/sites/cnn/business-favicon.ico'
FGI_URI = '/markets/fear-and-greed'

session = Session()


class ROUND(Enum):
    DAY = auto()
    HOUR = auto()


# modified from https://stackoverflow.com/a/24893252
def remove_empty_from_dict(d):
    if isinstance(d, dict):
        return dict((k, remove_empty_from_dict(v)) for k, v in d.items() if v and remove_empty_from_dict(v))
    elif isinstance(d, list):
        return [remove_empty_from_dict(v) for v in d if v and remove_empty_from_dict(v)]
    else:
        return d


def process_response(response, logger):
   # return HTTP error code
    if not response.ok:
        logger.error('Error from source')
        logger.debug('Dumping input:' + response.text)
        abort(
            500, description=f"HTTP status from source: {response.status_code}")

    try:
        return response.json()
    except ValueError:
        logger.error(f'"{query_object.query}" - invalid API response')
        logger.debug(
            f'"{query_object.query}" - dumping input: {response.text}')
        abort(
            500, description='Invalid API response')


def get_latest_fgi(logger, method=None):
    url = FGI_JSON_URL + FGI_JSON_URI

    logger.debug(f"Querying endpoint: {url}")
    try:
        response = session.get(url)
    except Exception as ex:
        logger.error(f"Exception: {ex}")
        abort(500, description=ex)

    response_json = process_response(response, logger)

    feed_title = 'Fear and Greed Index'

    json_feed = JsonFeedTopLevel(
        items=[],
        title=feed_title,
        home_page_url=CNN_URL + FGI_URI,
        favicon=CNN_URL + CNN_FAVICON_URI
    )

    fgi_historical_section = response_json.get('fear_and_greed_historical')
    fgi_historical_data = fgi_historical_section.get('data')
    latest_fgi = len(fgi_historical_data) - 1

    if fgi_historical_section:

        fgi_latest_obj = fgi_historical_data[latest_fgi]
        fgi_latest_value = fgi_latest_obj.get('y')
        fgi_latest_timestamp = fgi_latest_obj.get('x')
        fgi_latest_rating = fgi_latest_obj.get('rating')
        fgi_close_obj = fgi_historical_data[latest_fgi - 2]
        fgi_close_value = fgi_close_obj.get('y')
        fgi_close_timestamp = fgi_close_obj.get('x')
        fgi_close_rating = fgi_close_obj.get('rating')

        if method == ROUND.DAY:
            item_title = f"Fear & Greed Previous Close: {fgi_close_value} ({fgi_close_rating})"
            item_date_published = fgi_close_timestamp
        elif method == ROUND.HOUR:
            item_title = f"Fear & Greed Latest: {fgi_latest_value} ({fgi_latest_rating})"
            item_date_published = fgi_latest_timestamp

        converted_date = datetime.fromtimestamp(
            item_date_published / 1000)   # convert from millisecond to second

        item_content_text = 'As of ' + converted_date.strftime('%c')

        feed_item = JsonFeedItem(
            id=item_date_published,  # use timestamp as unique id
            url=url,
            title=item_title,
            date_published=converted_date.isoformat(),
            content_text=item_content_text
        )

        json_feed.items.append(feed_item)

    else:
        logger.warning('Historical values not found')

    return remove_empty_from_dict(asdict(json_feed))
