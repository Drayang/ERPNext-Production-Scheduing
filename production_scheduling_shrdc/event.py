from __future__ import unicode_literals

from six import print_
import frappe
import json
from frappe.utils import cint, getdate, formatdate, today
from frappe import throw, _
from frappe.model.document import Document

@frappe.whitelist()
def get_events(start, end, filters=None):
	"""Returns events for Gantt / Calendar view rendering.

	:param start: Start date-time.
	:param end: End date-time.
	:param filters: Filters (JSON).
	"""
	if filters:
		filters = json.loads(filters)
        
	else:
		filters = []

	if start:
		filters.append(['Holiday', 'holiday_date', '>', getdate(start)])
	if end:
		filters.append(['Holiday', 'holiday_date', '<', getdate(end)])
    

	return frappe.get_list('Holiday List',
		fields=['name', '`tabHoliday`.holiday_date', '`tabHoliday`.description', '`tabHoliday List`.color'],
		filters = filters,
		update={"allDay": 1})