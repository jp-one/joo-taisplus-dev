from odoo import models, fields, api
from .tais_service import TaisService
import logging

_logger = logging.getLogger(__name__)


class TaisImport(models.TransientModel):
    _name = "taisplus.tais.import"
    _description = "Import TAIS Codes"

    tais_codes = fields.Text(
        string="TAISコード(複数可)", required=True, help="複数のTAISコードを改行で区切って入力してください"
    )

    @api.model
    def fetch_tais_data(self, tais_code):
        taisCodeService: TaisService = self.env["taisplus.tais.service"]
        parts = tais_code.split("-")
        tais_url = taisCodeService.generate_tais_url(parts[0], parts[1])
        taisCode = taisCodeService.fetch_tais_product_details(tais_url)
        return taisCode

    def import_tais_codes(self):
        """Import TAIS codes from the entered text."""
        if not self.tais_codes:
            raise ValueError("No TAIS codes provided.")

        tais_code_list = [
            code.strip() for code in self.tais_codes.splitlines() if code.strip()
        ]

        taisCode = self.env["taisplus.tais"]
        taisCode = taisCode.sudo()

        for tais_code in tais_code_list:
            try:
                # Fetch data from the API
                data = self.fetch_tais_data(tais_code)

                # ccta95_id
                ccta95 = self.env["taisplus.ccta95"].search(
                    [("ccta95_code", "=", data.get("ccta95_code", ""))], limit=1
                )
                if ccta95:
                    data["ccta95_id"] = ccta95.id

                # rental_service
                data["rental_service"] = "R" + data.get("rental_service_code")
                # sales_service
                data["sales_service"] = "S" + data.get("sales_service_code")

                # Upsert
                existing_record = taisCode.search(
                    [("tais_code", "=", tais_code)], limit=1
                )
                if existing_record:
                    new_data = {
                        "name": data.get("product_name"),
                        "tais_code": tais_code,
                        "ccta95_id": data.get("ccta95_id"),
                        "model_number": data.get("model_number"),
                        "manufacturer": data.get("manufacturer"),
                        "rental_service": data.get("rental_service"),
                        "sales_service": data.get("sales_service"),
                        "image_url": data.get("image_url"),
                        "product_summary": data.get("product_summary"),
                        "is_discontinued": data.get("is_discontinued"),
                        "tais_url": data.get("tais_url"),
                    }
                    existing_record.write(
                        {
                            key: value
                            for key, value in new_data.items()
                            if value is not None
                        }
                    )
                else:
                    new_data = {
                        "name": data.get("product_name"),
                        "tais_code": tais_code,
                        "ccta95_id": data.get("ccta95_id"),
                        "model_number": data.get("model_number"),
                        "manufacturer": data.get("manufacturer"),
                        "rental_service": data.get("rental_service"),
                        "sales_service": data.get("sales_service"),
                        "image_url": data.get("image_url"),
                        "product_summary": data.get("product_summary"),
                        "is_discontinued": data.get("is_discontinued"),
                        "tais_url": data.get("tais_url"),
                    }
                    taisCode.create(
                        {
                            key: value
                            for key, value in new_data.items()
                            if value is not None
                        }
                    )
            except Exception as e:
                _logger.error(f"Error importing TAIS code {tais_code}: {e}")
