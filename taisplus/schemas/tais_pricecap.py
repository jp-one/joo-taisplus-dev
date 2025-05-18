from datetime import date
from typing import TypedDict


class TaisPriceCapItemDict(TypedDict):
    name: str
    date: date
    average_price: float
    price_cap: float
    currency: str


class TaisPriceCapDict(TypedDict):
    tais_code: str
    target_date: date
    target: TaisPriceCapItemDict
    future: TaisPriceCapItemDict
