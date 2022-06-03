from datetime import datetime
from enum import Enum, auto
from math import floor
from flask import abort
from requests import Session
from json_feed_data import JSONFEED_VERSION_URL, JsonFeedItem, JsonFeedTopLevel

import random


FGI_JSON_URL = 'https://production.dataviz.cnn.io'
FGI_JSON_URI = '/index/fearandgreed/graphdata'
CNN_URL = 'https://edition.cnn.com'
CNN_FAVICON_URI = '/media/sites/cnn/business-favicon.ico'
FGI_URI = '/markets/fear-and-greed'

session = Session()
user_agent = None


class ROUND(Enum):
    DAY = auto()
    HOUR = auto()
    HOUR_OPEN = auto()


def get_response_json(url, useragent_list, logger):
    global user_agent

    headers = {'Referer': CNN_URL}

    if useragent_list and not user_agent:
        user_agent = random.choice(useragent_list)
        logger.debug(
            f'Using user-agent: "{user_agent}"')

    if user_agent:
        headers['User-Agent'] = user_agent

    try:
        response = session.get(url, headers=headers)
    except Exception as ex:
        logger.error(f'Exception: {ex}')
        abort(500, description=ex)

    # return HTTP error code
    if not response.ok:
        user_agent = None
        if response.status_code == 418:
            logger.warning('Anti-scraping triggered')
            abort(response.status_code)
        else:
            logger.error('Error from source')
            logger.debug('Dumping input:' + response.text)
            abort(response.status_code)

    try:
        return response.json()
    except ValueError:
        logger.error('Invalid API response')
        logger.debug(
            f'Dumping input: {response.text}')
        abort(
            500,
            description='Invalid API response'
        )


def get_latest_fgi(logger, useragent_list, method=None):
    url = FGI_JSON_URL + FGI_JSON_URI

    response_json = get_response_json(url, useragent_list, logger)

    feed_title = 'Fear and Greed Index'

    generated_items = []

    fgi_historical_section = response_json.get('fear_and_greed_historical')
    fgi_historical_data = fgi_historical_section.get('data')
    latest_fgi = len(fgi_historical_data) - 1

    if fgi_historical_section:

        fgi_latest_obj = fgi_historical_data[latest_fgi]
        fgi_latest_value = fgi_latest_obj.get('y')
        # convert from millisecond to second
        fgi_latest_timestamp = fgi_latest_obj.get('x') / 1000
        fgi_latest_rating = fgi_latest_obj.get('rating')

        fgi_close_obj = fgi_historical_data[latest_fgi - 2]
        fgi_close_value = fgi_close_obj.get('y')
        # convert from millisecond to second
        fgi_close_timestamp = fgi_close_obj.get('x') / 1000
        fgi_close_rating = fgi_close_obj.get('rating')

        if method == ROUND.DAY:
            item_title = f"Fear & Greed Previous Close: {floor(fgi_close_value)} ({fgi_close_rating})"
        elif (method == ROUND.HOUR or method == ROUND.HOUR_OPEN):
            item_title = f"Fear & Greed Hourly: {floor(fgi_latest_value)} ({fgi_latest_rating})"
        else:
            item_title = f"Fear & Greed Latest: {floor(fgi_latest_value)} ({fgi_latest_rating})"

        if method == ROUND.DAY:
            converted_date = datetime.utcfromtimestamp(fgi_close_timestamp)
            item_timestamp = fgi_close_timestamp
        elif (method == ROUND.HOUR or method == ROUND.HOUR_OPEN):
            converted_date = datetime.utcfromtimestamp(
                fgi_latest_timestamp).replace(minute=0, second=0, microsecond=0)
            item_timestamp = converted_date.timestamp()
        else:
            converted_date = datetime.utcfromtimestamp(fgi_latest_timestamp)
            item_timestamp = fgi_latest_timestamp

        item_content_text = 'As of ' + converted_date.strftime('%c')

        feed_item = JsonFeedItem(
            id=str(item_timestamp),  # use timestamp as unique id
            url=CNN_URL + FGI_URI,
            title=item_title,
            date_published=converted_date.isoformat(),
            content_text=item_content_text
        )

        # for OPEN rounding methods, append item only when FGI is different from previous close
        if not (method == ROUND.HOUR_OPEN and fgi_latest_value == fgi_close_value):
            generated_items.append(feed_item)

    else:
        logger.warning('Historical values not found')

    json_feed = JsonFeedTopLevel(
        title=feed_title,
        items=generated_items,
        version=JSONFEED_VERSION_URL,
        home_page_url=CNN_URL + FGI_URI,
        favicon=CNN_URL + CNN_FAVICON_URI
    )

    return json_feed
