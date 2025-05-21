from dataclasses import dataclass
from typing import Any


@dataclass
class AidPriceData:
    price: float
    currency: str
    date_start: str
    target_datetime: str


@dataclass
class AidProductData:
    default_code: str
    product_name: str
    sales_price: AidPriceData
    purchase_price: AidPriceData
    tais_pricecap: Any # TaisPriceCapData
