from odoo import models
from datetime import date, datetime
from ..schemas import AidPriceDict, AidProductDict


class ProductService(models.AbstractModel):
    _name = "product_tais.product.service"
    _description = "Product Service"

    def _get_sales_price(self, product_tmpl_id, product_id, target_datetime):

        product_pricelist_item = self.env["product.pricelist.item"]
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
        product_pricelist_item.env.cr.execute(query, params)
        pricelist_item = product_pricelist_item.env.cr.fetchone()
        if pricelist_item:
            pricelist_item = product_pricelist_item.browse(pricelist_item[0])
            sales_price = pricelist_item.fixed_price
            sales_currency = pricelist_item.currency_id.name
            sales_date_start = pricelist_item.date_start
        else:
            sales_price = None
            sales_currency = None
            sales_date_start = None

        return AidPriceDict(
            price=sales_price,
            currency=sales_currency,
            date_start=sales_date_start,
            target_datetime=target_datetime,
        )

    def _get_purchase_price(self, product_tmpl_id, product_id, target_date):

        product_supplierinfo = self.env["product.supplierinfo"]
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
        product_supplierinfo.env.cr.execute(query, params)
        supplierinfo = product_supplierinfo.env.cr.fetchone()
        if supplierinfo:
            supplierinfo = product_supplierinfo.browse(supplierinfo[0])
            purchase_price = supplierinfo.price
            purchase_currency = supplierinfo.currency_id.name
            purchase_date_start = supplierinfo.date_start
        else:
            purchase_price = None
            purchase_currency = None
            purchase_date_start = None

        return AidPriceDict(
            price=purchase_price,
            currency=purchase_currency,
            date_start=purchase_date_start,
            target_datetime=target_date,
        )

    def _get_tais_price_cap(self, tais_code, target_date):
        
        priceListService = self.env["taisplus.pricelist.service"]
        taisPriceCap = priceListService.get_tais_price_cap(
            tais_code, target_date
        )
        return taisPriceCap


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
            return None

        # Product price
        sales_price = self._get_sales_price(
            product.product_tmpl_id.id, product.id, target_datetime
        )

        # Purchase price
        purchase_price = self._get_purchase_price(
            product.product_tmpl_id.id, product.id, target_date
        )

        # TAIS pricecap
        taisPriceCap = self._get_tais_price_cap(
            product.tais_code, target_date
        )

        return AidProductDict(
            default_code=default_code,
            product_name=product.name if product else None,
            sales_price=sales_price,
            purchase_price=purchase_price,
            tais_pricecap=taisPriceCap,
        )
