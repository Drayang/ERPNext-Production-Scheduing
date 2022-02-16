# -*- coding: utf-8 -*-
# Copyright (c) 2022, DCKY and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document

class FreppleSetting(Document):
	def get_params_and_url(self):
		params = {
			"USER": self.username,
			"PWD": self.get_password(fieldname="password", raise_exception=False),
			"SIGNATURE": self.authorization_header,

		}

		return params

