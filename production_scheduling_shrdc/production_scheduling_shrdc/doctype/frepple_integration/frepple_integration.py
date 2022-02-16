# -*- coding: utf-8 -*-
# Copyright (c) 2022, DCKY and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
# import frappe
from frappe.model.document import Document
import frappe 
import json
from frappe.integrations.utils import make_get_request, make_post_request, create_request_log
from frappe.utils import get_request_session

import requests
from requests.structures import CaseInsensitiveDict

from datetime import datetime

'''
Naming convention:
Get request: get_{frepple document}
Post request: post_{frepple document}
'''
class FreppleIntegration(Document):
	# @frappe.whitelist()
	def get_demand(self):
		api = 'demand'

		# url,headers = get_frepple_params(api=api,filter=None)

		''' With filtering'''
		filter=None
		# filter="?status=open"
		
		url,headers = get_frepple_params(api=api,filter=filter)
		# filter = None
		
		ro = make_get_request(url,headers=headers) #ro is a list type, so need [] to access
		# dt = datetime.fromisoformat(startdate)
		name = ro[0]['name']
		print(type(ro))
		dd = ro[0]['due']
		#convert iso8601 time type to datetime.datetime type
		dt = datetime.fromisoformat(dd)
		self.sales_order = name
		self.delivery_date = dt

		return ro

	@frappe.whitelist()
	def test(self):
		# doc = frappe.get_doc('Frepple Integration', doc['name']) #To get the current item	
		print(self.password)

		print(type(self.password))
		# print(type(doc.password))	
		# return doc.password


@frappe.whitelist()
def testing(doc):
	doc = json.loads(doc)
	print(doc)
	doc = frappe.get_doc('Frepple Integration', doc['name']) #To get the current item	
	print(type(doc.password))

	return doc.password


def make_put_request(url, auth=None, headers=None, data=None):
	if not auth:
		auth = ''
	if not data:
		data = {}
	if not headers:
		headers = {}

	try:
		s = get_request_session()
		frappe.flags.integration_request = s.put(url, data=data, auth=auth, headers=headers)
		frappe.flags.integration_request.raise_for_status()

		if frappe.flags.integration_request.headers.get("content-type") == "text/plain; charset=utf-8":
			return parse_qs(frappe.flags.integration_request.text)

		return frappe.flags.integration_request.json()
	except Exception as exc:
		frappe.log_error()
		raise exc

# @frappe.whitelist()
# def put_demand():
# 	if(frappe.get_doc("Frepple Setting").frepple_integration):
		
# 		# doc = frappe.get_doc('Sales Order', doc['name']) #To get the current doc
# 		data = json.dumps({
# 			"status": "closed", #default
# 		})
# 		api = "demand/SAL-ORD-2022-00033" #equivalent sales order
# 		url,headers = get_frepple_params(api=api,filter=None)
# 		output = make_put_request(url,headers=headers, data=data)
# 		frappe.msgprint(
# 			msg='Data have been updated.',
# 			title='Note',
# 		)

# 		return output






@frappe.whitelist()
def get_frepple_params(api=None,filter = None):
	if not api:
		api = "" #default get the demand(=sales order in ERPNext) list from frepple
	if not filter:
		filter = ""

	frepple_settings = frappe.get_doc("Frepple Setting")
	temp_url = frepple_settings.url.split("//")
	url1 = "http://"
	url2 = frepple_settings.username + ":" + frepple_settings.password + "@"
	url3 = temp_url[1] + "/api/input/"
	url4 = "/"
	# "/?format=json"
	# "/?format=api"

	#Concatenate the URL
	url = url1 + url2 + url3 + api + url4 + filter
	# example outcome : http://admin:admin@192.168.112.1:5000/api/input/manufacturingorder/

	headers= {
		'Content-type': 'application/json; charset=UTF-8',
		'Authorization': frepple_settings.authorization_header,
	}
	print(url+ "-------------------------------------------------------------------------")

	return url,headers


#Testing purpose GET request  
@frappe.whitelist()
def make_request():
	# url = 'https://httpbin.org/post' 
	url = 'https://jsonplaceholder.typicode.com/todos/1'

	# headers= {
	# 'Content-type': 'application/json; charset=UTF-8',
	# # 'Accept': 'text/html; q=1.0, */*',
	# 'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiYWRtaW4iLCJleHAiOjE2NDIzMjQzNzR9.0v2_RrP3G3XHAHiOK-KiWkjceSSkdqh1E6_huSv-BcI',
	# # 'user': 'admin',
	# # 'password': 'admin'
	# }
	url = 'http://admin:admin@192.168.112.1:5000/api/input/demand/?format=json'
	# url = 'http://192.168.112.1:5000/api/input/demand/?format=json'
	url = 'http://192.168.0.145:5000/api/input/demand/?format=json'
	# url = 'http://admin:admin@172.17.0.1:5000/api/input/demand/?format=json'
	# url = 'http://172.17.0.1:5000/api/input/demand/?format=json'


	headers= {
		'Content-type': 'application/json',
		'Authorization': "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyIjoiYWRtaW4iLCJleHAiOjE2NDM1OTI0OTR9.T6ClCybo9dGRvzuUusDoZM-JYco5DIe5aDOioV4ERH0",
	}
	abc = make_get_request(url,headers=headers)
	return abc


'''
# api = 'string' e.g 'manufacturingorder'
# filter = '?filter' e.g 'name=SALE-ORDER-005' ,'location=SHRDC&customer=Drayang'
'''
@frappe.whitelist()
def get_manufacturingorder():
	api = 'manufacturingorder'

	url,headers = get_frepple_params(api=api,filter=None)

	''' With filtering'''
	# filter = "?name=SAL-ORDER-0002"
	# filter = None
	# filter = "?status__contain=open"
	# url,headers = get_frepple_params(api=None,filter=filter)

	ro = make_get_request(url,headers=headers)
	startdate = ro[0]['startdate']
	#convert iso8601 time type to datetime.datetime type
	dt = datetime.fromisoformat(startdate)
	return ro


@frappe.whitelist()
def post_item(doc):
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		doc = json.loads(doc) #dict form
		doc = frappe.get_doc('Item', doc['name']) #To get the current item	
		
		''' Define the Frepple table you want to match'''
		api = "item" #equivalent to customer doctype
		
		url,headers = get_frepple_params(api=api,filter=None)
		
		'''Add the item_group to frepple to use it as the owner to ensure no request error happen'''
		data = json.dumps({
			"name": doc.item_group,
		})
		output = make_post_request(url,headers=headers, data=data)

		'''Add the actual item to frepple'''
		data = json.dumps({
			"name": doc.name,
			"owner":doc.item_group,
			"description":doc.item_name,
			"uom":doc.stock_uom,
			"cost":doc.valuation_rate,
		})
		output = make_post_request(url,headers=headers, data=data)
		
		frappe.msgprint(
			msg='Data have been exported to Frepple.',
			title='Note',
		)

		return output


@frappe.whitelist()
def post_location():
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		''' Define the Frepple table you want to match'''
		api = "location" 
		
		url,headers = get_frepple_params(api=api,filter=None)

		
		company_list = frappe.db.get_list('Company', # Find the Machine Status name via filter the workstation name
			fields =['name'],
		)
		for company in company_list:
			'''Add the company to the location table'''
			data = json.dumps({
				"name": company.name,
			})
			output = make_post_request(url,headers=headers, data=data)
		
		
		warehouse_list = frappe.db.get_list('Warehouse', # Find the Machine Status name via filter the workstation name
			fields =['name','company','parent_warehouse'],
		)
		for warehouse in warehouse_list:
			'''Add the warehouse location to the location table'''
			data = json.dumps({
				"name": warehouse.name,
				"owner":warehouse.parent_warehouse if (warehouse.parent_warehouse) else warehouse.company, 
				# If a warehouse is the parent warehouse, let its owner to be the company name
			})
			output = make_post_request(url,headers=headers, data=data)


		frappe.msgprint(
			msg='Data have been exported to Frepple.',
			title='Note',
		)

		return output


@frappe.whitelist()
def post_employee(doc):
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		doc = json.loads(doc) #dict form
		doc = frappe.get_doc('Employee', doc['name']) #To get the current item	
		
		if(doc.status == "Active"):
			''' Define the Frepple table you want to match'''
			api = "resource" #equivalent to employee doctype
			
			url,headers = get_frepple_params(api=api,filter=None)
			
			'''Add a null operator to frepple to use it as the owner to ensure no request error happen'''
			data = json.dumps({
				"name": "Operator",#default
			})
			output = make_post_request(url,headers=headers, data=data)

			'''Add the actual employee to frepple'''
			data = json.dumps({
				"name": doc.name,
				"description":doc.employee_name,
				"owner":"Operator" #default
			})
			output = make_post_request(url,headers=headers, data=data)
			
			frappe.msgprint(
				msg='Data have been exported to Frepple.',
				title='Note',
			)

			return output


@frappe.whitelist()
def post_workstation(doc):
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		
		''' Define the Frepple table you want to match'''
		api = "resource" #equivalent to employee doctype
		url,headers = get_frepple_params(api=api,filter=None)
		
		temp_doc = json.loads(doc) #dict form
		
		'''If doctype = BOM'''
		if (temp_doc['doctype'] == "BOM" and temp_doc['is_active'] ): # Only add an active BOM
			doc = frappe.get_doc('BOM', temp_doc['name']) #To get the current item	
			operations = doc.operations

			# Get the workstation
			for row in operations:
				d = frappe.get_doc('BOM Operation', row.name) #To access child doctype
				workstation = d.workstation
				'''Add the workstation to frepple'''
				data = json.dumps({
					"name": workstation,
				})

				output = make_post_request(url,headers=headers, data=data)

		'''If doctype = Workstation'''
		if (temp_doc['doctype'] == "Workstation"):
			doc = frappe.get_doc('Workstation', temp_doc['name']) #To get the current item	
			data = json.dumps({
				"name": doc.name,
			})

			output = make_post_request(url,headers=headers, data=data)

		frappe.msgprint(
			msg='Data have been exported to Frepple.',
			title='Note',
		)

		return output


@frappe.whitelist()
def post_customer(doc):
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		doc = json.loads(doc) #dict form
		doc = frappe.get_doc('Customer', doc['name']) #To get the current sales order	
		
		''' Define the Frepple table you want to match'''
		api = "customer" #equivalent to customer doctype
		
		url,headers = get_frepple_params(api=api,filter=None)

		'''To create a cutomer with Group type first to ensure no request error happen'''
		data = json.dumps({
			"name": doc.customer_group,
		})
		output = make_post_request(url,headers=headers, data=data)
		
		'''Create the actual customer we would like to add to'''
		data = json.dumps({
			"name": doc.name,
			"category":doc.customer_type,
			"owner":doc.customer_group
		})
		output = make_post_request(url,headers=headers, data=data)
		frappe.msgprint(
			msg='Data have been exported to Frepple.',
			title='Note',
		)

		return output


@frappe.whitelist()
def post_supplier(doc):
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		doc = json.loads(doc) #dict form
		doc = frappe.get_doc('Supplier', doc['name']) #To get the current sales order	
		
		''' Define the Frepple table you want to match'''
		api = "supplier" #equivalent to customer doctype
		
		url,headers = get_frepple_params(api=api,filter=None)
		
		'''Create the actual supplier we would like to add to'''
		data = json.dumps({
			"name": doc.name,
			"category":doc.supplier_group
		})

		output = make_post_request(url,headers=headers, data=data)
		frappe.msgprint(
			msg='Data have been exported to Frepple.',
			title='Note',
		)

		return output


@frappe.whitelist()
def post_demand(doc):
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		#parse: mean convert string to object/dictionary

		'''https://discuss.erpnext.com/t/how-to-call-external-web-service/40448/14 check this to
		check eval() and how to pass it argument in data variable
		'''

		# NOTE
		# throw in string as variable can work , e.g name = "SAL-ORDER-00012"
		# throw in integer as variable can work also
		# cannot pass in datetime
		# duetime = eval(datetime type) cannot work, eval only accept: string, code, byte

		# current_time = datetime.datetime.strptime(current_time,'%Y-%m-%d %H:%M:%S') #datetime field type pass in as string

		# duetime = datetime(2022,1,16,12,25,00)# datetime(year, month, day, hour, minute, second, microsecond)

		# duetime = duetime.isoformat() # Can be in any form

		# json.dumps convert object to json string
		doc = json.loads(doc) #dict form
		doc = frappe.get_doc('Sales Order', doc['name']) #To get the current sales order
		# doc = frappe.get_doc('Sales Order', 'SAL-ORD-2022-00033') #To get the current
		so_items = doc.items

		# Get the item and its quantity (assume only one item per sales order now)
		for row in so_items:
			d = frappe.get_doc('Sales Order Item', row.name) #To access child doctype
			quantity = d.qty
			item = d.item_name

			# doc = frappe.get_doc('Sales Order', doc['name']) #To get the current doc
			data = json.dumps({
				"name": doc.name,
				"description": "Item ordered by " + doc.customer_name, #default
				"category": "", #default
				"subcategory": "", #default
				"item": item,
				"customer": doc.customer_name,
				"location": "SHRDC", #default
				"due":  (doc.delivery_date.isoformat()+"T00:00:00"),
				"status": "open", #default
				"quantity": quantity,
				"priority": "10" #default
			})
			api = "demand" #equivalent sales order
			url,headers = get_frepple_params(api=api,filter=None)
			output = make_post_request(url,headers=headers, data=data)
			frappe.msgprint(
				msg='Data have been exported to Frepple.',
				title='Note',
			)

		return output


@frappe.whitelist()
def post_skill(doc):
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		doc = json.loads(doc) #dict form
		doc = frappe.get_doc('Skill', doc['name']) #To get the current sales order	
		
		''' Define the Frepple table you want to match'''
		api = "skill" #equivalent to customer doctype
		
		url,headers = get_frepple_params(api=api,filter=None)
		
		'''Create the actual supplier we would like to add to'''
		data = json.dumps({
			"name": doc.name,
		})

		output = make_post_request(url,headers=headers, data=data)
		frappe.msgprint(
			msg='Data have been exported to Frepple.',
			title='Note',
		)

		return output



@frappe.whitelist()
def post_resourceskill(doc):
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		
		''' Define the Frepple table you want to match'''
		api = "resourceskill" #equivalent to employee doctype
		url,headers = get_frepple_params(api=api,filter=None)
		
		doc = json.loads(doc) #dict form
		doc = frappe.get_doc('Employee Skill Map', doc['name']) #To get the current item	
		skill_list = doc.employee_skills

		# Get the workstation
		for row in skill_list:
			d = frappe.get_doc('Employee Skill', row.name) #To access child doctype
			'''Add the skill to frepple'''
			data = json.dumps({
				"resource":doc.employee,
				"location":"work in progress",
				"skill" : d.skill,
				"priority":5-d.proficiency, #use priority in frepple to define how proficiency the employee is
			})

			output = make_post_request(url,headers=headers, data=data)

		frappe.msgprint(
			msg='Data have been exported to Frepple.',
			title='Note',
		)

		return output


@frappe.whitelist()
def run_plan():
	if(frappe.get_doc("Frepple Setting").frepple_integration):
		
		filter = "/execute/api/runplan/?constraint=15&plantype=1&env=fcst,invplan,balancing,supply"
		frepple_settings = frappe.get_doc("Frepple Setting")
		temp_url = frepple_settings.url.split("//")
		url = "http://"+ frepple_settings.username + ":" + frepple_settings.password + "@" + temp_url[1] + filter
		print(url + "-----------------------------------------------------------------------")
		headers= {
			'Content-type': 'application/json; charset=UTF-8',
			'Authorization': frepple_settings.authorization_header,
		}

		output = make_post_request(url,headers=headers, data=None)

		frappe.msgprint(
			msg='Plan have been runned succesffully',
			title='Success',
		)

		return output




# @frappe.whitelist()
# def get_demand(self):
# 	api = 'demand'

# 	# url,headers = get_frepple_params(api=api,filter=None)

# 	''' With filtering'''
# 	filter=None
# 	filter="?status=open"
	
# 	url,headers = get_frepple_params(api=None,filter=filter)
# 	# filter = None
	
# 	ro = make_get_request(url,headers=headers)
# 	# dt = datetime.fromisoformat(startdate)
# 	name = ro[0]['name']
# 	print(type(ro))
# 	dd = ro[0]['due']
# 	#convert iso8601 time type to datetime.datetime type
# 	dt = datetime.fromisoformat(dd)
# 	self.delivery_date = dt

# 	return ro