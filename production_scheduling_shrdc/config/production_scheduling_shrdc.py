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
                #     "type": "doctype",
                #     "name": "Frepple Integration",
                #     "label": "Frepple Integration",
                #     "onboard": 2,
                # },
            ]
        },
        {
            "label": _("Frepple Integration"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Frepple Integration",
                    "label": "Frepple Integration",
                    "onboard": 1,
                    # "dependencies": ["Item"],
                },
                                {
                    "type": "doctype",
                    "name": "Frepple Settings",
                    "label": "Frepple Settings",
                    "onboard": 2,
                },
            ]
        }
    ]
    return config