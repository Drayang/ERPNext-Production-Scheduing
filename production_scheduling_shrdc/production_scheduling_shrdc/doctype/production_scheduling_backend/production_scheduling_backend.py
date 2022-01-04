# -*- coding: utf-8 -*-
# Copyright (c) 2021, DCKY and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe import get_all, msgprint, _
from frappe.utils import add_to_date ,getdate,today,now #utils now and today is string form
from frappe.utils import flt, cint, formatdate, comma_and, time_diff_in_seconds, to_timedelta
import datetime


from frappe.model.document import Document
# from erpnext.erpnext.manufacturing.doctype.workstation.workstation import 
from erpnext.manufacturing.doctype.production_plan.production_plan import ProductionPlan
from erpnext.manufacturing.doctype.workstation.workstation import get_default_holiday_list
#from frappe.utils.background_jobs import start_worker
from frappe.utils.data import time_diff_in_hours

class WorkstationHolidayError(frappe.ValidationError): pass
class ProductionSchedulingBackend(Document):
	pass

def get_all_info(doc,current_time):
	# current_time = current datetime , pass in as arg because now() and datetime.datetime.now() cant get the correct now
	current_time = datetime.datetime.strptime(current_time,'%Y-%m-%d %H:%M:%S') #current_time pass in as datetime type
	#pp_date = today()
	pp_date = datetime.datetime.strptime(today(),'%Y-%m-%d') #convert to datetime type

	# To access the current from field type. doc is in dict type, access using doc['fieldname']
	doc = json.loads(doc) #dict form
	doc = frappe.get_doc('Production Plan', doc['name']) #To get the current doc
	po_items = doc.po_items #access the production plan item child doctype

	# Obtain the total operation time and working hours of workstation
	total_op_time,start_time,end_time = read_bom(po_items,pp_date)

	#last_datetime=datetime.datetime(1900,1,1,0,0,0) #initialise datetime.datetime
	# Find the latest datetime we can assigned to the work order,meanwhile,update the start_time and end_time
	last_datetime,start_time,end_time = find_datetime(pp_date,current_time,start_time,end_time)
	
	info = dict()
	info['last_datetime']=last_datetime
	info['start_time']=start_time
	info['end_time']=end_time
	info['total_op_time']=total_op_time
	info['po_items']=po_items
	info['pp_date']=pp_date
	info['current_time']=current_time
	
	return info

@frappe.whitelist()
def production_scheduling(doc,current_time):

	machine_status,valid_ms,machine = check_workstation_status(doc) #Tell us whether the machine is under maintainance or sudden downtime,valid_ms = True:Machine available, False: unavailable
	valid_emp = check_employee(doc) # Check employee availability
	info = {}

	if (valid_ms and valid_emp): #Only schedule if machine and employee valid

		info = get_all_info(doc,current_time)
		po_items = info['po_items']
		last_datetime = info['last_datetime']
		start_time =info['start_time']
		end_time=info['end_time']
		total_op_time= info['total_op_time']
		pp_date=info['pp_date']
		current_time = info['current_time']

		predict_op_time = ''
		for row in po_items:
			d = frappe.get_doc('Production Plan Item', row.name) #To access child doctype

			last_datetime,temp_datetime,exceed,start_time,end_time = check_within_operating_hours(d,current_time,last_datetime,pp_date,start_time,end_time,total_op_time,machine)

			if (~exceed): #only run if we no exceed the day
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
		'valid_ms':valid_ms,
		'valid_emp':valid_emp,
		#'abc':abc,
		#'abcd':abcd,
		#'abcde':abcde,
		'machine':machine,
		'doc':doc,
	}

@frappe.whitelist()
def update_production_plan(doc,current_time):
	#Valid_ms: True = Up(available), False = Down(unavailable)
	machine_status,valid_ms,machine = check_workstation_status(doc) #Tell us whether the machine is under maintainance or sudden downtime,valid = True:Machine available, False: unavailable
	valid_emp = check_employee(doc) # Check employee availability
	affected_idx = 0

	#Should have a way to get the real downtime but i self define one first
	downtime = datetime.datetime(2022,1,4,12,25,00)# datetime(year, month, day, hour, minute, second, microsecond)

	info = {} #intialise dict

	#Change: True = Can reschedule production plan, False = Cannot reschdeule
	change = False #Becareful ~False = -2, no True, so the condition check need directly ==False
	if (valid_ms == False): # Only run if the workstation is unavailable(under Down)
		if (machine_status == "Down: Scheduling Maintenance"): #Four type of Down status,only this status do not have planned end date for me to reschedule production plan
			change = False 
		else: #Can change the production plan if the status == other 3
			
			info = get_all_info(doc,current_time)
			po_items = info['po_items']
			last_datetime = info['last_datetime']
			start_time =info['start_time']
			end_time=info['end_time']
			total_op_time= info['total_op_time']
			pp_date=info['pp_date']
			current_time = info['current_time']

			#Find the maintenance work order for the break down machine
			mwo = frappe.db.get_list('Maintenance Work Order', # Find the Machine Status name via filter the workstation name
				filters ={
					'workstation':machine,
				},
				fields =['name'],
			)

			if (len(mwo) != 0): #mean the desired maintenance work order is exist
				change = True
				mwo_doc = frappe.get_doc('Maintenance Work Order',mwo[0])

				#Get the planned complete date of the maintanance, and add 5 minute delay to it
				last_datetime = add_to_date(mwo_doc.planned_complete_date,minutes=5,as_datetime=True) #add a five minute delay
				#### To set a scheduled maintenance datetime and try out
				#last_datetime = datetime.datetime(2022,1,5,12,20,00)
				
				
				#temp = datetime.datetime.now()
				# abc = len(po_items) # can get the lens //
				
				# Find the affected work order
				affected_idx = find_affected_wo(po_items,downtime)
				print('affected_idx')
				print(affected_idx)

				#update the date until all parameter date are the same with the last_datetime date
				pp_date, start_time, end_time = update_time(pp_date,start_time,end_time,last_datetime)

				# loop through the po_items table, look for the work order that are affected and update the new planned start date
				for row in po_items:
					d = frappe.get_doc('Production Plan Item', row.name) #To access child doctype
					# abc = d.idx #/// can get
					print(d.idx)
					print(last_datetime)
					# temp = d.planned_start_date
					# if (d.idx ==affected_idx): #Force the work order to have the planned start datetime we want
					# 	work_order = frappe.db.get_list('Work Order', 
					# 		filters ={
					# 			'sales_order':d.sales_order
					# 		},
					# 		fields =['name'],
					# 	)
					# 	# To set the field of the work order
					# 	frappe.db.set_value('Work Order', work_order[0].name, 'planned_start_date', last_datetime)
					# 	# To refresh the work order doctype and store the value
					# 	document = frappe.get_doc('Work Order', work_order[0].name)
					# 	document.save(ignore_permissions=True, ignore_version=True)
					# 	document.reload()
					if (d.idx >= affected_idx) and (affected_idx != 0): #0 indicate no affected wo
						last_datetime,temp_datetime,exceed,start_time,end_time = check_within_operating_hours(d,current_time,last_datetime,pp_date,start_time,end_time,total_op_time,machine)
						if (~exceed): #only run if we no exceed the day
							d.db_set('planned_start_date', last_datetime)
							last_datetime = temp_datetime #Assign the new datetime to the last_datetime
							d.save(ignore_permissions=True)
							d.reload()
				
		
	frappe.response['message'] = {
		'valid_ms':valid_ms,
		'change':change,
		'affected_idx':affected_idx,
		'machine':machine,
		'info':info,
		'doc':doc,
	}


@frappe.whitelist()
def update_work_order(doc):
	# To access the current from field type. doc is in dict type, access using doc['fieldname']
	doc = json.loads(doc) #dict form
	doc = frappe.get_doc('Production Plan', doc['name']) #To get the current doc
	po_items = doc.po_items #access the production plan item child doctype

	for row in po_items:
		d = frappe.get_doc('Production Plan Item', row.name) #To access child doctype

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
def check_workstation_status(doc):
	# To access the current from field type. doc is in dict type, access using doc['fieldname']
	doc = json.loads(doc) #dict form
	doc = frappe.get_doc('Production Plan', doc['name']) #To get the current doc
	po_items = doc.po_items #access the production plan item child doctype
	bom_no = po_items[0].bom_no	 # assume all link to the same BOM
	bom = frappe.get_doc('BOM', bom_no)

	# Status list
	machine_status=''
	machine = ''
	status_1 = "Up: Idle" #valid_ms:True
	status_2 = "Up: Running" #valid_ms:True
	status_3 = "Down: Scheduling Maintenance"  #valid_ms:False
	status_4 = "Down: Waiting For Maintenance"  #valid_ms:False
	status_5 = "Down: Under Maintenance" #valid_ms:False
	status_6 = "Down: Post Inspection" #valid_ms:False

	valid_ms = True
	if (doc.check_machine_status):#if the checkbox is ticked
		for row in bom.operations: #Loop through the bom.operation to access each workstation
			workstation = frappe.get_doc('Workstation',row.workstation) #Get the Workstation we want
			machine_status_name = frappe.db.get_list('Machine Status', # Find the Machine Status name via filter the workstation name
				filters ={
					'workstation':workstation.workstation_name,
				},
				fields =['name'],
			)
			document = frappe.get_doc('Machine Status',machine_status_name[0].name) #Get the machine status doctype we want
			machine = workstation.workstation_name
			machine_status = document.machine_status

			#If the machine is under Down, directly return valid_ms = False
			if (machine_status == status_3 ) or (machine_status == status_4 ) or (machine_status == status_5 ) or (machine_status == status_6 ): 
				valid_ms = False
				return machine_status,valid_ms,machine
	
	# valid_ms : True= for all Up , False = for all down

		
	# frappe.response['message'] = {
	# 	'valid_ms':valid_ms,
	# 	#'abcd':abcd,
	# 	#'abcde':abcde,
	# 	'doc':doc,
	# }
	# r.message[0] = status,r.message[1]=valid_ms
	# if only return one variable, can do r.message.status
	return machine_status,valid_ms,machine

@frappe.whitelist()
def check_duplicate_wo(doc):
	# To access the current from field type. doc is in dict type, access using doc['fieldname']
	doc = json.loads(doc) #dict form
	doc = frappe.get_doc('Production Plan', doc['name']) #To get the current doc
	po_items = doc.po_items #access the production plan item child doctype
	
	######### Condition Checking to avoid duplicate work order###########
	manufacture_qty = 0
	row_to_remove=[] #store the index of row that need to be remove (first index coutn from 0)
	for row in po_items:
		cd = frappe.get_doc('Production Plan Item', row.name) #To access child doctype
		exist = frappe.db.exists({ #check whether the document exist or not by checking the sales_order
			'doctype': 'Work Order',
			'sales_order': cd.sales_order,
		})

		if (exist):
			#manufactuer_qty = existed work order's qty
			manufacture_qty = frappe.db.get_value('Work Order', {'sales_order': cd.sales_order}, ['qty'])

		planned_qty = cd.planned_qty-manufacture_qty
		
		if (planned_qty == 0): # If the existed qty - planned_qty = 0, indicating same amount of qty ady be created, so we should remove the work order in the po_items
			row_to_remove.append(cd.sales_order)

	frappe.response['message'] = {
		'row_to_remove':row_to_remove,
		#'abcde':abcde,
		'doc':doc,
	}

@frappe.whitelist()
def check_employee(doc):
	valid_emp = 0
	valid_emp_skill = 1
	valid_emp_emount = 1

	doc = json.loads(doc) #dict form
	doc = frappe.get_doc('Production Plan', doc['name']) #To get the current doc
	po_items = doc.po_items #access the production plan item child doctype

	bom,workstation = get_bom_detail(po_items)
	if (doc.check_employee):#if the checkbox to check employee is ticked
		valid_emp_emount = check_emp_amout(workstation)
		valid_emp_skill = check_emp_skill(workstation)

	if (valid_emp_emount) and (valid_emp_skill):
		valid_emp = 1	

	return valid_emp

def check_emp_skill(workstation):

	valid_emp_skill = 1 #initialise
	skill_rq = [] #store each workstation name as the key for dict
	emp_list = frappe.db.get_list('Employee Skill Map', 
			fields =['name'],
		)
	emp_with_skill = {} #initialise a list of dictionary to store the available employee for each skill
	idx = 0 #to access the skill_rq list
	''' The idea here is to loop through the workstation, get the skill required(skill_req) and store them into the list
	Then loop through the Employee Skill Map> Employee> Employee Skill to see whether there is any match skill
	If yes, append a value "1" to the particular dict key (the key is the skill name)
	In the end, sum each key value, if each key value >1 mean valid
	## Limitation: 1. Cannot check duplicate employee if the employee have more than 1 skill needed.
	'''
	if (len(emp_list) != 0):
		for workstation in workstation:
			temp_list= []
			skill_rq.append((workstation.split("-"))[1]) #Workstation name : Workstation 1-Loading, [1] is to obtain loading
			emp_with_skill[skill_rq[idx]] = [] #initialise the dict key with an empty list
			''' https://www.geeksforgeeks.org/python-ways-to-create-a-dictionary-of-lists/ refer to this to understand why i need 
			to define a empty list and append it first'''
			
			for row in emp_list:
				doc = frappe.get_doc('Employee Skill Map',row.name)
				skill = doc.employee_skills
				for skill in doc.employee_skills:
					if (skill_rq[idx] == skill.skill): #check whehter the employee have the skill we want(skill_rq)
						temp_list.append(1)
						print(skill_rq[idx])
						print(skill.skill)
			
			emp_with_skill[skill_rq[idx]].append(temp_list)
			idx = idx+1

	print(emp_with_skill)
	for key in skill_rq:
		print(sum(emp_with_skill[key][0]))
		if (sum(emp_with_skill[key][0]) < 1):
			valid_emp_skill = 0
			return valid_emp_skill
	print(valid_emp_skill)
	return valid_emp_skill
	
def check_emp_amout(workstation):

	valid_emp_amount = 0 #initialise

	emp_list = frappe.db.get_list('Employee', 
		filters =
		{
			'status':'active'
		},
		fields =['name'],
		# order_by = 'planned_start_date desc'
	)

	if len(emp_list)>= len(workstation):
		valid_emp_amount = 1

	print(len(emp_list))
	print(len(workstation))
	print(valid_emp_amount)
	return valid_emp_amount
	

################## update_production_plan ###################
def find_affected_wo(po_items,downtime):
	affected_idx = 0 # e.g = 1 mean first row WO get affected
	inRange = 0
	end_idx = len(po_items) #size of the po_items list = the last idx
	for row in po_items:
		d = frappe.get_doc('Production Plan Item', row.name) #To access child doctype
		if (d.idx != 1): #First row do not run this function
			#Check the previous loop (e.g 2nd loop but we actually finding for 1st work order) whether it is scheduled within the downtime
			inRange = time_in_range(temp_planned_start_date,d.planned_start_date,downtime)
			print('inRange')
			print(inRange)
			print(downtime)
			print(temp_planned_start_date)
			print(d.planned_start_date)
			if (inRange): #if inRange, indicating this WO and the consequene work order are all affected
				affected_idx = d.idx-1 #minus 1 so it fulfill the "2nd loop but is refering 1st work order" idea
				return affected_idx

		if (d.idx == end_idx): # We should explicitly run a time_in_range func for the very last row 
			#assume loop till last row if still not within then no work order is affected
			return affected_idx #should be 0
		# 	inRange = time_in_range(temp_planned_start_date,d.planned_start_date,downtime)

		temp_planned_start_date = d.planned_start_date

def time_in_range(start,end,downtime):
	inRange = 0
	
	if (downtime<=end) and (downtime >= start):
		inRange = 1

	return inRange

################## update_production_plan end ###################
################## production_scheduling ##################
def check_within_operating_hours(cd,current_time,last_datetime,pp_date,start_time,end_time,total_op_time,machine):
	delay = 5
	exceed = 0
	isHoliday = 0 #Workstation is holiday or not
	remainder = 0
	split_qty = 0 #planeed qty that have been split
	######### Condition Checking to avoid duplicate work order###########
	# manufacture_qty = 0
	# exist = frappe.db.exists({ #check whether the document exist or not
	# 	'doctype': 'Work Order',
	# 	'sales_order': cd.sales_order,
	# })
	# if (exist):
	# 	manufacture_qty = frappe.db.get_value('Work Order', {'sales_order': cd.sales_order}, ['qty'])

	#planned_qty = cd.planned_qty-manufacture_qty
	#cd.planned_qty = planned_qty
	# if (planned_qty == 3):
	# 	frappe.delete_doc('Production Plan Item', row['name'])
	# 	delay = 0

	planned_qty = cd.planned_qty
	predict_op_time = planned_qty*total_op_time + delay # Calculate the total operation time needed
	temp_datetime = add_to_date(last_datetime,minutes=(predict_op_time),as_datetime=True) #Predict the end datetime

	isHoliday = check_workstation_for_holiday(machine, pp_date.date(),pp_date.date())
	print('isHoliday')
	print(isHoliday)
	while(isHoliday):#update until the date that is not holiday for the machine
		pp_date, start_time, end_time = update_time(pp_date,start_time,end_time,None) #update all the time by one day
		isHoliday = check_workstation_for_holiday(machine, pp_date.date(),pp_date.date())

	print('Inside the check within')
	print(last_datetime)
	print(temp_datetime)
	print(end_time)
	if start_time and end_time:
		# datetime.datetime(2021, 12, 28, 12, 00, 00)
		if (temp_datetime< end_time): # check whether the operation time over the working hour
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
			
			pp_date, start_time, end_time = update_time(pp_date,start_time,end_time,None) #update all the time by one day
			#### try to add a new child row after this then we can remove all the part below include exceed check,
			#### the new child doctype should have the value of the remainder
			#### [i think is impossible because we are in a loop of po_items, add new child doctype cannot have real time
			#### changes]
			last_datetime,start_time,end_time = find_datetime(pp_date,current_time,start_time,end_time) #Get the word order list of next day
			print('end_time')
			print(end_time)	
		
			last_datetime,temp_datetime,exceed_temp,start_time,end_time = check_within_operating_hours(cd,current_time,last_datetime,pp_date,start_time,end_time,total_op_time,machine)
			
			# last_datetime = temp_datetime
			# Reassign back the last_datetime so it match what we want


	return last_datetime,temp_datetime,exceed,start_time,end_time

def find_datetime(pp_date,current_time,start_time,end_time):

	if (pp_date == ''):
		pp_date = today()

	#if last_datetime == initialise, mean this is the first time we finding last_datetime, run normal check
	#if (last_datetime == datetime.datetime(1900,1,1,0,0,0)):
	wo_listt = frappe.db.get_list('Work Order', 
		filters =
		[[
			'planned_start_date', 'between', [pp_date, pp_date] #Limit the filter only on that particular day where we want to the work order
		]],
		fields =['qty','planned_start_date'],
		order_by = 'planned_start_date desc'
	)
	# # Find the total wo_qty on that particular day
	# wo_qty = 0
	# for i in range(0, len(wo_listt)):    
	# 	wo_qty = wo_qty + wo_listt[i].qty  
	
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
		ignore,start_time,end_time = update_time(pp_date, start_time,end_time,None) #update the start and end time of workstation
	# else:
	# 	if (last_datetime > end_time):
	# 		last_datetime = add_to_date(start_time,days=1,as_datetime=True)
	# 		ignore,start_time,end_time = update_time(pp_date, start_time,end_time) #update the start and end time of workstation


	return last_datetime,start_time,end_time

def read_bom(po_items,pp_date):
	bom_no = po_items[0].bom_no	 # access list then only access the attribute

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
	# start_time = str(pp_date)+ ' '+str(start_temp)
	# start_time = datetime.datetime.strptime(start_time,'%Y-%m-%d %H:%M:%S')
	# end_time = str(pp_date)+ ' '+str(end_temp)
	# end_time = datetime.datetime.strptime(end_time,'%Y-%m-%d %H:%M:%S')
	print('read_bom')

	start_time = datetime.datetime.strftime(pp_date,'%Y-%m-%d')+ ' '+str(start_temp)
	start_time = datetime.datetime.strptime(start_time,'%Y-%m-%d %H:%M:%S')
	end_time = datetime.datetime.strftime(pp_date,'%Y-%m-%d')+ ' '+str(end_temp)
	end_time = datetime.datetime.strptime(end_time,'%Y-%m-%d %H:%M:%S')

	#end_time = datetime.datetime(2021, 12, 28, 12, 20, 00)
	
	print(end_time)


	return total_op_time,start_time,end_time

#Update all datetime by 1 day while running the else loop of checkwithin opearting time
def update_time(pp_date, start_time,end_time,last_datetime):

	if (last_datetime == None): 
		pp_date = add_to_date(pp_date,days = 1,as_datetime=True)
		start_time = add_to_date(start_time,days=1,as_datetime=True)
		end_time = add_to_date(end_time,days=1,as_datetime=True)
	else:
		while(last_datetime.date()>pp_date.date()): #to make sure the date are all sync with last_datetime
			pp_date = add_to_date(pp_date,days = 1,as_datetime=True)
			start_time = add_to_date(start_time,days=1,as_datetime=True)
			end_time = add_to_date(end_time,days=1,as_datetime=True)
	'''
	# Else loop is specialy make for the update_production_plan because if I want to force the planned complete_date = last_datetime
	# to be the first option while assign to the planned_start_date, and if the complete date is not on the same day
	# after running the check_within_operation func, the last_datetime will update based on the first WO time on the day, which is
	# not valid since no work order should be created that day (if follow the checking of my function, it will take start time as default time)
	'''
	return pp_date,start_time,end_time

################## production_scheduling end ##################
def get_bom_detail(po_items):
	bom_no = po_items[0].bom_no	 # access list then only access the attribute

	bom = frappe.get_doc('BOM', bom_no)
	
	#Access only the first row of operations's workstation [assume all workstation have same working hours]
	# workstation = frappe.get_doc('Workstation',bom.operations[0].workstation)

	workstation= []
	for row in bom.operations:
		workstation.append(frappe.get_value('Workstation',row.workstation,'name'))
	return bom,workstation

#from_datetime,to_datetime = datetime.date type
def check_workstation_for_holiday(workstation, from_datetime, to_datetime):
	holiday_list = frappe.db.get_value("Workstation", workstation, "holiday_list")
	isHoliday = 0
	if holiday_list and from_datetime and to_datetime:
		applicable_holidays = []
		for d in frappe.db.sql("""select holiday_date from `tabHoliday` where parent = %s
			and holiday_date between %s and %s """,
			(holiday_list, from_datetime, to_datetime)):
				applicable_holidays.append(formatdate(d[0]))

		print(applicable_holidays)
		if applicable_holidays:
			isHoliday = 1
			# frappe.throw(_("Workstation is closed on the following dates as per Holiday List: {0}")
			# 	.format(holiday_list) + "\n" + "\n".join(applicable_holidays), WorkstationHolidayError)
	return isHoliday
