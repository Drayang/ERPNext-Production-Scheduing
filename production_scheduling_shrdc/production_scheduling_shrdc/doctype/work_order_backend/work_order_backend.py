# -*- coding: utf-8 -*-
# Copyright (c) 2021, DCKY and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe import msgprint, _
from frappe.utils import add_to_date ,getdate,today,now
from frappe.utils import flt, cint, formatdate, comma_and, time_diff_in_seconds, to_timedelta
import datetime

from frappe.model.document import Document
# from erpnext.erpnext.manufacturing.doctype.workstation.workstation import 
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from erpnext.manufacturing.doctype.workstation.workstation import get_default_holiday_list,check_if_within_operating_hours
#from frappe.utils.background_jobs import start_worker
from frappe.utils.data import time_diff_in_hours

class WorkOrderBackend(Document):
	pass

@frappe.whitelist()
def work_order_scheduling(doc,pp_isLinked):
	pp_date = today()
	abc = ''
	# To access the current from field type. doc is in dict type, access using doc['fieldname']
	doc = json.loads(doc) #dict form

	if not doc['production_plan']:
		abc = 'hi'

	frappe.response['message'] = {
		'abc':abc,
		# 'abcd':abcd,
		#'abcde':abcde,
		'doc':doc,
	}


