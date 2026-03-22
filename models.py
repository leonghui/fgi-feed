from pydantic import BaseModel
from datetime import datetime


class Quote(BaseModel):
    x: datetime
    y: float
    rating: str


class Historical(BaseModel):
    timestamp: datetime
    score: float
    rating: str
    data: list[Quote]


class Current(BaseModel):
    score: float
    rating: str
    timestamp: datetime
    previous_close: float
    previous_1_week: float
    previous_1_month: float
    previous_1_year: float


class GraphData(BaseModel):
    fear_and_greed: Current
    fear_and_greed_historical: Historical
