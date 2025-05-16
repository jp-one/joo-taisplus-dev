from typing import Tuple, TypedDict, Union

from pytz import utc
from odoo import http
from odoo.http import request
import json
from datetime import datetime, date
from ..models import ProductService

from odoo import http
from odoo.http import request

def date_serializer(obj):
    """Custom serializer for date objects."""
    if isinstance(obj, date):
        return obj.isoformat()
    return obj  # Return the object as-is if it's not serializable


class ApiController(http.Controller):

    class ErrorResponse(TypedDict):
        error: str
        details: str

    @http.route(
        "/taisplus/api/product/<string:default_code>/<string:target_datetime>",
        type="http",
        auth="api_key",
        methods=["GET"],
        csrf=False,
    )
    def get_product(self, default_code, target_datetime, **kwargs):

        product_service: ProductService = request.env["product_tais.product.service"]
        
        try:
            # target_date = datetime.strptime(target_date, "%Y-%m-%d").date()
            target_date = datetime.fromisoformat(target_datetime).date()
            target_datetime = datetime.fromisoformat(target_datetime).astimezone(utc)

        except ValueError:
            return request.make_response(
                json.dumps(
                    ApiController.ErrorResponse(
                        error="Invalid datetime format.",
                        details="Expected ISO8601, yyyy-mm-ddThh:mm:ss+09:00.",
                    )
                ),
                headers=[("Content-Type", "application/json")],
                status=400,
            )

        tais_product = product_service.get_tais_product(
            default_code, target_datetime, target_date
        )

        if not tais_product:
            return request.make_response(
                json.dumps(
                    ApiController.ErrorResponse(
                        error="Product not found.",
                        details="Product code: {}".format(default_code),
                    )
                ),
                headers=[("Content-Type", "application/json")],
                status=404,
            )

        return request.make_response(
            json.dumps(tais_product, default=date_serializer),
            headers=[("Content-Type", "application/json")],
            status=200,
        )
