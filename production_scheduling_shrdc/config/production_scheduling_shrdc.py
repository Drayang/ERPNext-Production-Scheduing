from __future__ import unicode_literals
from frappe import _

def get_data():
    config = [
        {
            "label": _("Production Scheduling"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Production Scheduling Backend",
                    "onboard": 1,
                    # "dependencies": ["Item"],
                },
                # {
                #     "type": "page",
                #     "name": "barcode-scanner",
                #     "label": "Barcode Scanner",
                #     "onboard": 1,
                # },
            ]
        }
    ]
    return config