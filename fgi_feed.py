from cssutils import parseStyle
from datetime import datetime
from pytz import timezone

import requests
from bs4 import BeautifulSoup
from flask import abort

JSONFEED_VERSION_URL = 'https://jsonfeed.org/version/1.1'
MONEY_CNN_URL = 'https://money.cnn.com'
FGI_URI = '/data/fear-and-greed/'
FGI_FAVICON_URI = '/favicon.ico'
CNN_TZ = timezone('US/Eastern')


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

    # assume same year as query time
    datetime_obj = default_tz.localize(
        datetime_obj.replace(year=datetime.now().year))

    return datetime_obj.astimezone(timezone('UTC'))


def get_latest_fgi(logger):
    page_response = requests.get(MONEY_CNN_URL + FGI_URI)

    # return HTTP error code
    if not page_response.ok:
        abort(500, f"HTTP status from source: {page_response.status_code}")

    page_content = page_response.text

    page_soup = BeautifulSoup(page_content, features='html.parser')
    feed_title = page_soup.title.text
    feed_url = MONEY_CNN_URL + FGI_URI

    output = {
        'version': JSONFEED_VERSION_URL,
        'title': feed_title,
        'home_page_url': feed_url,
        'favicon': MONEY_CNN_URL + FGI_FAVICON_URI
    }

    header = page_soup.head

    try:
        page_desc = header.select_one("meta[name='description']")['content']
        if page_desc:
            output['description'] = page_desc.strip()
    except TypeError:
        logger.info('Description not found')

    chart_section = page_soup.find(id='needleChart')

    items_list = []

    if chart_section:
        fgi_values = chart_section.select('ul > li')
        fgi_value = next(iter(fgi_values), None)

        date_section = page_soup.find(id='needleAsOfDate')

        fgi_datetime = extract_datetime(date_section.text, CNN_TZ)

        item = {
            'id': fgi_datetime.isoformat('T'),  # use timestamp as unique id
            'url': feed_url,
            'title': feed_title,
            'date_published': fgi_datetime.isoformat('T'),
            'content_text': fgi_value.text
        }

        items_list.append(item)

    else:
        logger.warning('Chart section not found')

    output['items'] = items_list

    return output
