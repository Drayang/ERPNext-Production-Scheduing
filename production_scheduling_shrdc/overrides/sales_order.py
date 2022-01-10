from erpnext.selling.doctype.sales_order.sales_order import SalesOrder
from frappe import msgprint
import frappe
from frappe import _

class CustomSalesOrder(SalesOrder):
    def on_submit(self):
        self.my_custom_code()

    def validate(self):
        self.my_custom_code()

    def my_custom_code(self):
        frappe.msgprint(_("Hi how are you mtfker"))
        print('Hi how are yo mtfker')

