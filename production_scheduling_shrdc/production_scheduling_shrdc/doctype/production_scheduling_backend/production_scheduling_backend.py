# -*- coding: utf-8 -*-
# Copyright (c) 2021, DCKY and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe import msgprint, _
from frappe.utils import add_to_date ,getdate,today,now #utils now and today is string form
from frappe.utils import flt, cint, formatdate, comma_and, time_diff_in_seconds, to_timedelta
import datetime


from frappe.model.document import Document
# from erpnext.erpnext.manufacturing.doctype.workstation.workstation import 
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from erpnext.manufacturing.doctype.workstation.workstation import get_default_holiday_list,check_if_within_operating_hours
#from frappe.utils.background_jobs import start_worker
from frappe.utils.data import time_diff_in_hours

class ProductionSchedulingBackend(Document):
	pass


@frappe.whitelist()
def production_scheduling(doc,current_time):
	# current_time = current datetime , pass in as arg because now() and datetime.datetime.now() cant get the correct now
	current_time = datetime.datetime.strptime(current_time,'%Y-%m-%d %H:%M:%S') #current_time pass in as datetime type
	pp_date = today()


	# To access the current from field type. doc is in dict type, access using doc['fieldname']
	doc = json.loads(doc) #dict form
	po_items = doc['po_items'] # list

	# Obtain the total operation time and working hours of workstation
	total_op_time,start_time,end_time = read_bom(po_items,pp_date)

	# Obtain the total work order quantity of the particular date and
	wo_qty,last_datetime,start_time,end_time = find_datetime(pp_date,current_time,start_time,end_time)
	# abcd = add_to_date(now(),hours=8,as_datetime=True)
	abc = last_datetime
	# datetime.datetime.now(ZoneInfo("Malaysia/Kuala_Lumpur"))
	#planned_datetime = []
	
	predict_op_time = ''
	for row in po_items:
		d = frappe.get_doc('Production Plan Item', row['name']) #To access child doctype

		# 	slot_length = (to_timedelta(end_time or "") - to_timedelta(start_time or "")).total_seconds() #give working hour in second
		last_datetime,temp_datetime,exceed,start_time,end_time = check_within_operating_hours(d,current_time,last_datetime,pp_date,start_time,end_time,total_op_time)
		abcd = exceed

		if (~exceed): #only run if we exceed the day
			d.planned_start_date = last_datetime # Set the child doctype planned start date as the last_datetime
			last_datetime = temp_datetime #Assign the new datetime to the last_datetime
		
		# d.planned_start_date = last_datetime # Set the child doctype planned start date as the last_datetime
		# last_datetime = temp_datetime #Assign the new datetime to the last_datetime
		print(temp_datetime)
		print(last_datetime)
		d.save(ignore_permissions=True, ignore_version=True)
		d.reload()
		

	#abcd= planned_datetime
	#abc = get_default_holiday_list()


	#to access the date : r.message.pp_setup
	#'name you want access': variable that you want be assigned to in this python file
	frappe.response['message'] = {
		'wo_qty':wo_qty,
		#'wo_listt':wo_listt,
		'last_datetime':last_datetime,
		'abc':abc,
		'abcd':abcd,
		#'abcde':abcde,
		'doc':doc,
	}


# production_scheduling_shrdc.production_scheduling_shrdc.doctype.production_scheduling_backend.production_scheduling_backend.(method)

# def create_new_row():

	### can refer work order maybe ..... frappe.new_doc and doc.update
	# def create_job_card(work_order, row, qty=0, auto_create=False):
	# doc = frappe.new_doc("Job Card")
	# doc.update({
	# 	'work_order': work_order.name,
	# 	'operation': row.get("operation"),
	# 	'workstation': row.get("workstation"),
	# 	'posting_date': nowdate(),
	# 	'for_quantity': qty or work_order.get('qty', 0),
	# 	'operation_id': row.get("name"),
	# 	'bom_no': work_order.bom_no,
	# 	'project': work_order.project,
	# 	'company': work_order.company,
	# 	'wip_warehouse': work_order.wip_warehouse
	# })

@frappe.whitelist()
def update_work_order(doc):
	# To access the current from field type. doc is in dict type, access using doc['fieldname']
	doc = json.loads(doc) #dict form
	po_items = doc['po_items'] # list

	for row in po_items:
		d = frappe.get_doc('Production Plan Item', row['name']) #To access child doctype

		print(d.sales_order)

		work_order = frappe.db.get_list('Work Order', 
			filters ={
				'sales_order':d.sales_order
			},
			fields =['name'],
		)
		# To set the field of the work order
		frappe.db.set_value('Work Order', work_order[0].name, 'planned_start_date', d.planned_start_date)
		# To refresh the work order doctype and store the value
		document = frappe.get_doc('Work Order', work_order[0].name)
		document.save(ignore_permissions=True, ignore_version=True)
		document.reload()

	frappe.response['message'] = {
		#'abc':abc,
		#'abcd':abcd,
		#'abcde':abcde,
		'doc':doc,
	}

@frappe.whitelist()
def update_production_plan(doc):
	# To access the current from field type. doc is in dict type, access using doc['fieldname']
	doc = json.loads(doc) #dict form
	po_items = doc['po_items'] # list

	temp = datetime.datetime.now()
	# abc = len(po_items) # can get the lens //
	for row in po_items:
		d = frappe.get_doc('Production Plan Item', row['name']) #To access child doctype
		abc = d.idx #/// can get
		temp = d.planned_start_date
		d.db_set('planned_start_date', now())
		d.save(ignore_permissions=True)
		d.reload()
		

	frappe.response['message'] = {
		'abc':abc,
		#'abcd':abcd,
		#'abcde':abcde,
		'doc':doc,
	}

def time_in_range(start,end,time):
	inRange = 0
	
	if (time<end) and (time > start):
		inRange = 1

	return inRange

def check_within_operating_hours(cd,current_time,last_datetime,pp_date,start_time,end_time,total_op_time):
	delay = 5
	exceed = 0
	remainder = 0
	split_qty = 0 #planeed qty that have been split
	######### Condition Checking to avoid duplicate work order###########
	manufacture_qty = 0
	exist = frappe.db.exists({ #check whether the document exist or not
		'doctype': 'Work Order',
		'sales_order': cd.sales_order,
	})
	if (exist):
		manufacture_qty = frappe.db.get_value('Work Order', {'sales_order': cd.sales_order}, ['qty'])

	#planned_qty = cd.planned_qty-manufacture_qty
	#cd.planned_qty = planned_qty
	# if (planned_qty == 3):
	# 	frappe.delete_doc('Production Plan Item', row['name'])
	# 	delay = 0

	##############################################
	# print('Hi')
	# print(last_datetime)
	planned_qty = cd.planned_qty
	predict_op_time = planned_qty*total_op_time + delay # Calculate the total operation time needed
	temp_datetime = add_to_date(last_datetime,minutes=(predict_op_time),as_datetime=True) #Predict the end datetime
	# print('temp_datetime')
	# print(temp_datetime)
	# print(end_time)
	# print('logic')
	# print(temp_datetime <end_time)
	if start_time and end_time:
		# datetime.datetime(2021, 12, 28, 12, 00, 00)
		if (temp_datetime < end_time): # check whether the operation time over the working hour
			#planned_datetime.append(last_datetime)			
			last_datetime = last_datetime
			#doc.db_set('planned_start_date', last_datetime, commit=True) #cannot use because my doc is not a doctype 
		else:
			exceed = 1 #Represent we exceed today
			# time_left = time_diff_in_hours(end_time,last_datetime)*60
			# split_qty = round(round(time_left)/total_op_time)
			# remainder = planned_qty - split_qty
			# cd.planned_qty = split_qty #
			
			cd.planned_start_date = last_datetime
			
			pp_date, start_time, end_time = update_time(pp_date,start_time,end_time) #update all the time by one day
			#### try to add a new child row after this then we can remove all the part below include exceed check,
			#### the new child doctype should have the value of the remainder
			#### [i think is impossible because we are in a loop of po_items, add new child doctype cannot have real time
			#### changes]
			wo_qty,last_datetime,start_time,end_time = find_datetime(pp_date,current_time,start_time,end_time) #Get the word order list of next day
			
			last_datetime,temp_datetime,exceed_temp,start_time,end_time = check_within_operating_hours(cd,current_time,last_datetime,pp_date,start_time,end_time,total_op_time)
			# last_datetime = temp_datetime
			# Reassign back the last_datetime so it match what we want


	return last_datetime,temp_datetime,exceed,start_time,end_time


def find_datetime(pp_date,current_time,start_time,end_time):

	if (pp_date == ''):
		pp_date = today()

	wo_listt = frappe.db.get_list('Work Order', 
		filters =
		[[
			'planned_start_date', 'between', [pp_date, pp_date] #Limit the filter only on that particular day where we want to the work order
		]],
		fields =['qty','planned_start_date'],
		order_by = 'planned_start_date desc'
	)
	# Find the total wo_qty on that particular day
	wo_qty = 0
	for i in range(0, len(wo_listt)):    
		wo_qty = wo_qty + wo_listt[i].qty  
	
	# Find the very last manufacture time on that date
	#last_datetime = "" #The latest date
	if (len(wo_listt)!= 0): #if we have work order on that particular day
		last_datetime = wo_listt[0].planned_start_date #get the latest date
		last_datetime = add_to_date(last_datetime,minutes=5,as_datetime=True)
	else:
		last_datetime= start_time #set the first operation datetime at the start working hour of the workstation

	#condition check whether the last_datetime is before current datetime
	#current_time = datetime.datetime.strptime(now(),'%Y-%m-%d %H:%M:%S.%f') #now() is string type
	# current_time = datetime.datetime.now()
	if (last_datetime < current_time):
		last_datetime = add_to_date(current_time,minutes=10,as_datetime=True) #Planned the start datetime 10 minute later
	if (last_datetime > end_time):
		last_datetime = add_to_date(start_time,days=1,as_datetime=True)
		ignore,start_time,end_time = update_time(pp_date, start_time,end_time) #update the start and end time of workstation
	
	return wo_qty,last_datetime,start_time,end_time

def read_bom(po_items,pp_date):
	bom_no = po_items[0]['bom_no']	 # access list then only access the attribute

	bom = frappe.get_doc('BOM', bom_no)
	total_op_time = 0
	if bom.operations:
		for row in bom.operations:
			total_op_time = total_op_time + row.time_in_mins

	#Access only the first row of operations's workstation [assume all workstation have same working hours]
	workstation = frappe.get_doc('Workstation',bom.operations[0].workstation)

	for row in workstation.working_hours:
		if row.start_time and row.end_time:
			start_temp = row.start_time
			end_temp = row.end_time
	
	# Convert the datetime.timedelta format into datetime.datetime fomr
	start_time = str(pp_date)+ ' '+str(start_temp)
	start_time = datetime.datetime.strptime(start_time,'%Y-%m-%d %H:%M:%S')
	end_time = str(pp_date)+ ' '+str(end_temp)
	end_time = datetime.datetime.strptime(end_time,'%Y-%m-%d %H:%M:%S')
	
	#end_time = datetime.datetime(2021, 12, 28, 12, 20, 00)


	return total_op_time,start_time,end_time

#Update all datetime by 1 day while running the else loop of checkwithin opearting time
def update_time(pp_date, start_time,end_time):
	pp_date = add_to_date(pp_date,days = 1,as_datetime=True)
	start_time = add_to_date(start_time,days=1,as_datetime=True)
	end_time = add_to_date(end_time,days=1,as_datetime=True)

	return pp_date,start_time,end_time

def is_within_operating_hours(workstation,operation, from_datetime, to_datetime):
	operation_length = time_diff_in_seconds(to_datetime, from_datetime)
	workstation = frappe.get_doc("Workstation", workstation)
	
	if not workstation.working_hours:
		return

	for working_hour in workstation.working_hours:
		if working_hour.start_time and working_hour.end_time:
			slot_length = (to_timedelta(working_hour.end_time or "") - to_timedelta(working_hour.start_time or "")).total_seconds()
			if slot_length >= operation_length:
				return

	frappe.throw(_("Operation {0} longer than any available working hours in workstation {1}, break down the operation into multiple operations").format(operation, workstation.name), NotInWorkingHoursError)
	


