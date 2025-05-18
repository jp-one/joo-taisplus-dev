from typing import Any, TypedDict


class AidPriceDict(TypedDict):
    price: float
    currency: str
    date_start: str
    target_datetime: str


class AidProductDict(TypedDict):
    default_code: str
    product_name: str
    sales_price: AidPriceDict
    purchase_price: AidPriceDict
    tais_pricecap: Any  # TaisPriceCapDict
