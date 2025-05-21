from dataclasses import dataclass
from datetime import date
from typing import Any


@dataclass
class AidPriceData:
    target_datetime: date
    price: float
    currency: str
    date_start: date
    date_end: date


@dataclass
class AidVenderPriceData(AidPriceData):
    vendor_name: str
    vendor_product_code: str
    vendor_product_name: str


@dataclass
class AidProductData:
    default_code: str
    product_name: str
    sales_price: AidPriceData
    purchase_price: AidVenderPriceData
    tais_pricecap: Any  # TaisPriceCapData
