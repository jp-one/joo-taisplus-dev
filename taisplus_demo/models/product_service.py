from dataclasses import asdict
import json

import pytz

from pytz import utc
from odoo import api, models
from datetime import date, datetime
from ..schemas import AidPriceData, AidVenderPriceData, AidProductData

# from taisplus.models.pricelist_item import PriceListItem
# from taisplus.models.pricelist_service import PriceListService
# from addons.product.models.product_supplierinfo import SupplierInfo


def date_serializer(obj):
    """Custom serializer for date objects."""
    if isinstance(obj, date):
        return obj.isoformat()
    return obj  # Return the object as-is if it's not serializable

class ProductService(models.AbstractModel):
    _name = "product_tais.product.service"
    _description = "Product Service"

    def _get_sales_price(
        self, product_tmpl_id: int, product_id: int, target_datetime: datetime
    ):

        product_pricelist_item_model = self.env[
            "product.pricelist.item"
        ]  # type: PriceListItem
        query = (
            "SELECT id FROM product_pricelist_item"
            + " WHERE active AND min_quantity = 0 AND compute_price = 'fixed'"
            + "   AND (product_tmpl_id = %s or product_tmpl_id is null)"
            + "   AND (product_id = %s or product_id is null)"
            + "   AND (date_start <= %s or date_start is null)"
            + "   AND (date_end >= %s or date_end is null)"
            + " ORDER BY date_start desc nulls last, date_end asc nulls last, product_id asc nulls last, product_tmpl_id asc nulls last"
        )
        params = (
            product_tmpl_id,  # product_tmpl_id
            product_id,  # product_id
            target_datetime,  # date_start
            target_datetime,  # date_end
        )
        product_pricelist_item_model.env.cr.execute(query, params)
        pricelist_item = product_pricelist_item_model.env.cr.fetchone()
        if pricelist_item:
            pricelist_item = product_pricelist_item_model.browse(pricelist_item[0])
            return AidPriceData(
                target_datetime=target_datetime,
                price=(
                    pricelist_item.fixed_price if pricelist_item.fixed_price else None
                ),
                currency=pricelist_item.currency_id.name,
                datetime_start=(
                    pricelist_item.date_start if pricelist_item.date_start else None
                ),
                datetime_end=(
                    pricelist_item.date_end if pricelist_item.date_end else None
                ),
            )

        return AidPriceData(
            target_datetime=target_datetime,
            price=None,
            currency=None,
            datetime_start=None,
            datetime_end=None,
        )

    def _get_purchase_price(
        self, product_tmpl_id: int, product_id: int, target_date: date
    ):

        product_supplierinfo_model = self.env[
            "product.supplierinfo"
        ]  # type: SupplierInfo
        query = (
            "SELECT id FROM product_supplierinfo"
            + " WHERE min_qty = 0"
            + "   AND (product_tmpl_id = %s or product_tmpl_id is null)"
            + "   AND (product_id = %s or product_id is null)"
            + "   AND (date_start <= %s or date_start is null)"
            + "   AND (date_end >= %s or date_end is null)"
            + " ORDER BY date_start desc nulls last, date_end asc nulls last, product_id asc nulls last, product_tmpl_id asc nulls last"
        )
        params = (
            product_tmpl_id,  # product_tmpl_id
            product_id,  # product_id
            target_date,  # date_start
            target_date,  # date_end
        )
        product_supplierinfo_model.env.cr.execute(query, params)
        supplierinfo = product_supplierinfo_model.env.cr.fetchone()
        if supplierinfo:
            supplierinfo = product_supplierinfo_model.browse(
                supplierinfo[0]
            )  # type: SupplierInfo
            return AidVenderPriceData(
                target_date=target_date,
                price=supplierinfo.price,
                currency=supplierinfo.currency_id.name,
                date_start=supplierinfo.date_start if supplierinfo.date_start else None,
                date_end=supplierinfo.date_end if supplierinfo.date_end else None,
                vendor_name=(
                    supplierinfo.partner_id.name
                    if supplierinfo.partner_id.name
                    else None
                ),
                vendor_product_code=(
                    supplierinfo.product_code if supplierinfo.product_code else None
                ),
                vendor_product_name=(
                    supplierinfo.product_name if supplierinfo.product_name else None
                ),
            )

        return AidVenderPriceData(
            target_date=target_date,
            price=None,
            currency=None,
            date_start=None,
            date_end=None,
            vendor_name=None,
            vendor_product_code=None,
            vendor_product_name=None,
        )

    def _get_tais_price_cap(self, tais_code: str, target_date: date):

        price_list_service_model = self.env[
            "taisplus.pricelist.service"
        ]  # type: PriceListService
        taisPriceCap = price_list_service_model.get_tais_price_cap(
            tais_code, target_date
        )
        return taisPriceCap

    @api.model
    def get_tais_product(
        self, default_code: str, target_datetime: datetime, target_date: date
    ):
        # default_code (Internal Reference)
        product_product = self.env["product.product"]
        product = product_product.search(
            [
                ("default_code", "=", default_code),
                ("product_tmpl_id.detailed_type", "=", "tais_product"),
            ],
            limit=1,
        )

        if not product:
            return AidProductData(
                default_code=default_code,
                product_name=None,
                sales_price=None,
                purchase_price=None,
                tais_pricecap=None,
            )

        # Get product name in user's language
        user_lang = self.env.user.lang or "en_US"
        product_name = product.with_context(lang=user_lang).name

        # Product price
        sales_price = self._get_sales_price(
            product.product_tmpl_id.id, product.id, target_datetime
        )

        # Purchase price
        purchase_price = self._get_purchase_price(
            product.product_tmpl_id.id, product.id, target_date
        )

        # TAIS pricecap
        taisPriceCap = self._get_tais_price_cap(product.tais_code, target_date)

        return AidProductData(
            default_code=default_code,
            product_name=product_name,
            sales_price=sales_price,
            purchase_price=purchase_price,
            tais_pricecap=taisPriceCap,
        )
    
    @api.model
    def get_tais_product_json(
        self, default_code: str, date_string: str
    ):
        """
        Returns TAIS product information as a JSON string.

        Args:
            default_code (str): The internal reference code of the product.
            date_string (str): The target date and time in ISO format (e.g., '2024-05-25T12:00:00').
                You can also specify only the date (e.g., '2024-05-25'). In this case, the time will be set to 00:00:00.

        Returns:
            str: A JSON string containing product details, sales price, purchase price, and TAIS price cap.

        Raises:
            ValueError: If the product with the given default_code is not found.

        The method converts the input date string to the user's timezone, retrieves product data,
        and serializes it to JSON, handling date objects appropriately.
        """
        dt = datetime.fromisoformat(date_string)
        user_tzinfo = pytz.timezone(self.env.user.tz)
        if dt.tzinfo is None:
            dt_user = user_tzinfo.localize(dt)
        else:
            dt_user = dt.astimezone(user_tzinfo)
        dt_date = dt_user.date()
        dt_datetime = dt_user.astimezone(utc)
        aidProductData = self.get_tais_product(default_code, dt_datetime, dt_date)
        return json.dumps(asdict(aidProductData), default=date_serializer)
