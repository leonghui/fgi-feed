from requests import Session
from requests.models import Response

from config import logger
from pydantic import BaseModel
import requests_cache

CATALOG_URL = "https://code.cdn.mozilla.net/devices/devices.json"


class Device(BaseModel):
    name: str
    width: int
    height: int
    pixelRatio: float
    userAgent: str
    touch: bool
    os: str


class Devices(BaseModel):
    TYPES: list[str]
    phones: list[Device]
    tablets: list[Device]
    laptops: list[Device]
    televisions: list[Device]


requests_cache.install_cache(cache_name="/tmp/catalog_cache", expire_after=86400)


def get_useragent_list() -> list[str]:
    logger.debug(msg=f"Querying endpoint: {CATALOG_URL}")
    catalog_response: Response = Session().get(url=CATALOG_URL)

    if not catalog_response.ok:
        logger.warning(msg="Unable to get useragent list.")
        return []
    devices: Devices = Devices.model_validate(obj=catalog_response.json())
    return (
        [phone.userAgent for phone in devices.phones]
        if devices.phones
        else [tablet.userAgent for tablet in devices.tablets]
    )


useragent_list: list[str] = get_useragent_list()
