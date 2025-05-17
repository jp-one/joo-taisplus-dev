from odoo import models
from datetime import date

from .pricelist_item import PriceListItem
from ..schemas.tais_pricecap import TaisPriceCapDict, TaisPriceCapItemDict


class PriceListService(models.AbstractModel):
    _name = "taisplus.pricelist.service"
    _description = "TAIS Code Price List Service"

    def get_tais_price_cap(
        self,
        tais_code: str,
        target_date: date,
    ) -> TaisPriceCapDict:

        # Fetch target and previous records
        target = self._get_tais_price_cap_target(tais_code, target_date)

        # Determine target or minimum
        future = self._get_tais_price_cap_target_or_future(
            target, tais_code, target_date
        )

        return TaisPriceCapDict(
            tais_code=tais_code if tais_code else None,
            target_date=target_date,
            target=target,
            future=future,
        )

    def _get_tais_price_cap_target_or_future(
        self, target: TaisPriceCapItemDict | None, tais_code: str, target_date: date
    ):
        future = self._get_tais_price_cap_future(tais_code, target_date)
        if future == None:
            return target
        if target == None:
            return future
        if target.price_cap > future.price_cap:
            return future
        return target

    def _get_tais_price_cap_future(self, tais_code: str, target_date: date):
        priceListItem: PriceListItem = self.env["taisplus.pricelist.item"]
        record = priceListItem.search(
            [("tais_code", "=", tais_code), ("tais_code_date", ">", target_date)],
            order="price_cap asc",
            limit=1,
        )
        future = None
        if record:
            future = TaisPriceCapItemDict(
                name=record.pricelist_id.name,
                date=record.tais_code_date,
                average_price=record.average_price,
                price_cap=record.price_cap,
                currency=record.currency_id.name,
            )
        return future

    def _get_tais_price_cap_target(
        self,
        tais_code: str,
        target_date: date,
    ):
        priceListItem: PriceListItem = self.env["taisplus.pricelist.item"]
        record = priceListItem.search(
            [("tais_code", "=", tais_code), ("tais_code_date", "<=", target_date)],
            order="tais_code_date desc",
            limit=1,
        )
        target = None
        if record:
            target = TaisPriceCapItemDict(
                name=record.pricelist_id.name,
                date=record.tais_code_date,
                average_price=record.average_price,
                price_cap=record.price_cap,
                currency=record.currency_id.name,
            )
        return target
