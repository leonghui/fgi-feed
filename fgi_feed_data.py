from datetime import datetime
from typing import TypedDict


class FgiQuote(TypedDict):
    timestamp: float
    value: float
    rating: str
    value_text: str
    datetime: datetime
