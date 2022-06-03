from datetime import datetime
from enum import Enum, auto
from math import floor
from flask import abort
from requests import Session
from json_feed_data import JSONFEED_VERSION_URL, JsonFeedItem, JsonFeedTopLevel
from fgi_feed_data import FgiQuote
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


def get_fgi_quote(input) -> FgiQuote:
    value = input.get('y')
    rating = input.get('rating')
    timestamp = input.get('x') / 1000

    return {
        'value': value,
        'rating': rating,
        'value_text': f"{floor(value)} ({rating})",
        'timestamp': timestamp,
        'datetime': datetime.utcfromtimestamp(timestamp),
    }


def get_latest_fgi(logger, useragent_list, method=None):
    url = FGI_JSON_URL + FGI_JSON_URI

    response_json = get_response_json(url, useragent_list, logger)

    feed_title = 'Fear and Greed Index'

    generated_items = []

    fgi_historical_section = response_json.get('fear_and_greed_historical')
    fgi_historical_data = fgi_historical_section.get('data')
    latest_fgi = len(fgi_historical_data) - 1

    if fgi_historical_section:

        latest_quote = get_fgi_quote(fgi_historical_data[latest_fgi])
        closing_quote = get_fgi_quote(fgi_historical_data[latest_fgi - 2])

        if method == ROUND.DAY:
            round_title = 'Previous Close: '
        elif (method == ROUND.HOUR or method == ROUND.HOUR_OPEN):
            round_title = 'Hourly: '
        else:
            round_title = 'Latest: '

        if method == ROUND.DAY:
            fgi_value_title = closing_quote['value_text']
        else:
            fgi_value_title = latest_quote['value_text']

        if method == ROUND.DAY:
            converted_date = closing_quote['datetime']
            item_timestamp = closing_quote['timestamp']
        elif (method == ROUND.HOUR or method == ROUND.HOUR_OPEN):
            converted_date = latest_quote['datetime'].replace(
                minute=0, second=0, microsecond=0)
            item_timestamp = converted_date.timestamp()
        else:
            converted_date = latest_quote['datetime']
            item_timestamp = latest_quote['timestamp']

        feed_item = JsonFeedItem(
            id=str(item_timestamp),  # use timestamp as unique id
            url=CNN_URL + FGI_URI,
            title='Fear & Greed ' + round_title + fgi_value_title,
            date_published=converted_date.isoformat(),
            content_text='As of ' + converted_date.strftime('%c')
        )

        # for OPEN rounding methods, append item only when FGI is different
        # from previous close
        if not (method == ROUND.HOUR_OPEN and
                latest_quote['value'] == closing_quote['value']
                ):
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
