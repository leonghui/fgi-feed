from datetime import datetime
from enum import Enum
from math import floor
import random

from fastapi.exceptions import HTTPException
from requests.models import Response
from requests.sessions import Session

from config import CNN_FAVICON_URI, CNN_URL, FGI_JSON_URI, FGI_JSON_URL, FGI_URI, logger
from json_feed_data import JSONFEED_VERSION_URL, JsonFeedItem, JsonFeedTopLevel
from models import GraphData, Quote
from mozilla_devices import useragent_list

session: Session = Session()


class ROUNDING(Enum):
    daily = "daily"
    hourly = "hourly"
    hourly_open = "hourly_open"
    none = None


def get_response(url) -> Response:
    headers: dict[str, str] = {"Referer": CNN_URL}

    user_agent: str = random.choice(seq=useragent_list)
    logger.debug(msg=f'Using user-agent: "{user_agent}"')
    headers["User-Agent"] = user_agent

    try:
        response: Response = session.get(url, headers=headers)
    except Exception as ex:
        logger.error(msg=f"Exception: {ex}")
        raise HTTPException(status_code=500, detail=ex)

    # return HTTP error code
    if not response.ok:
        if response.status_code == 418:
            logger.warning(msg="Anti-scraping triggered")
            raise HTTPException(response.status_code)
        else:
            logger.error(msg="Error from source")
            logger.debug(msg="Dumping input:" + response.text)
            raise HTTPException(response.status_code)

    return response


class Formatter:
    latest: Quote
    closing: Quote
    title_map: dict[ROUNDING, str] = {
        ROUNDING.daily: "Previous Close:",
        ROUNDING.hourly: "Hourly:",
        ROUNDING.hourly_open: "Hourly:",
    }

    def __init__(self, latest, closing: Quote) -> None:
        self.latest = latest
        self.closing = closing

    def get_title_text(self, method: ROUNDING | None) -> str:
        quote: Quote = self.closing if method == ROUNDING.daily else self.latest
        quote_text: str = f"{floor(quote.y)} ({quote.rating})"
        return (
            f"{self.title_map.get(method)} {quote_text}"
            if method
            else f"Latest: {quote_text}"
        )

    def get_date(self, method: ROUNDING | None) -> datetime:
        date_map: dict[ROUNDING, datetime] = {
            ROUNDING.daily: self.closing.x,
            ROUNDING.hourly: self.latest.x.replace(minute=0, second=0, microsecond=0),
            ROUNDING.hourly_open: self.latest.x.replace(
                minute=0, second=0, microsecond=0
            ),
        }
        return date_map.get(method, datetime.now()) if method else datetime.now()


def get_latest_fgi(method: ROUNDING | None) -> JsonFeedTopLevel:
    url = FGI_JSON_URL + FGI_JSON_URI

    response: Response = get_response(url)

    graph_data: GraphData = GraphData.model_validate(obj=response.json())

    latest: Quote = graph_data.fear_and_greed_historical.data[-1]
    closing: Quote = graph_data.fear_and_greed_historical.data[-2]
    formatter: Formatter = Formatter(latest, closing)

    quote_date: datetime = formatter.get_date(method)

    feed_item: JsonFeedItem = JsonFeedItem(
        id=str(int(quote_date.timestamp())),  # use timestamp as unique id
        url=CNN_URL + FGI_URI,
        title="Fear & Greed " + formatter.get_title_text(method),
        date_published=quote_date.isoformat(),
        content_text="As of " + quote_date.strftime(format="%c"),
    )

    # for OPEN rounding methods, append item only when FGI is different
    # from previous close
    generated_items: list[JsonFeedItem] = []

    if not (method == ROUNDING.hourly_open and latest.y == closing.y):
        generated_items.append(feed_item)

    json_feed: JsonFeedTopLevel = JsonFeedTopLevel(
        title="Fear and Greed Index",
        items=generated_items,
        version=JSONFEED_VERSION_URL,
        home_page_url=CNN_URL + FGI_URI,
        favicon=CNN_URL + CNN_FAVICON_URI,
    )

    return json_feed
