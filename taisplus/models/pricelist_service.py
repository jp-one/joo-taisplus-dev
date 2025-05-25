from dataclasses import asdict
import json
from odoo import api, models
from datetime import date
from typing import Optional
from ..schemas.tais_pricecap import TaisPriceCapData, TaisPriceCapItemData
from .pricelist_item import PriceListItem


def date_serializer(obj):
    """Custom serializer for date objects."""
    if isinstance(obj, date):
        return obj.isoformat()
    return obj  # Return the object as-is if it's not serializable


class PriceListService(models.AbstractModel):
    _name = "taisplus.pricelist.service"
    _description = "TAIS Code Price List Service"

    def get_tais_price_cap(
        self,
        tais_code: str,
        target_date: date,
    ) -> TaisPriceCapData:
        target = self._get_tais_price_cap_item(tais_code, target_date, is_future=False)
        future = self._get_tais_price_cap_item(tais_code, target_date, is_future=True)
        selected = self._select_target_or_future(target, future)
        return TaisPriceCapData(
            tais_code=tais_code or None,
            target_date=target_date,
            target=target,
            future=selected,
        )

    def _get_tais_price_cap_item(
        self,
        tais_code: str,
        target_date: date,
        is_future: bool = False,
    ) -> Optional[TaisPriceCapItemData]:
        priceListItem = self.env["taisplus.pricelist.item"]  # type: PriceListItem
        domain = [
            ("tais_code", "=", tais_code),
            (
                ("tais_code_date", ">", target_date)
                if is_future
                else ("tais_code_date", "<=", target_date)
            ),
        ]
        order = "price_cap asc" if is_future else "tais_code_date desc"
        record = priceListItem.search(domain, order=order, limit=1)
        if not record:
            return None
        return TaisPriceCapItemData(
            name=record.pricelist_id.name,
            date=record.tais_code_date,
            average_price=record.average_price,
            price_cap=record.price_cap,
            currency=record.currency_id.name,
        )

    def _select_target_or_future(
        self,
        target: Optional[TaisPriceCapItemData],
        future: Optional[TaisPriceCapItemData],
    ) -> Optional[TaisPriceCapItemData]:
        if not future:
            return target
        if not target:
            return future
        return future if target.price_cap > future.price_cap else target

    @api.model
    def get_tais_price_cap_json(self, tais_code: str, target_date: date):
        taisPriceCapData = self.get_tais_price_cap(tais_code, target_date)
        return json.dumps(asdict(taisPriceCapData), default=date_serializer)
