// Copyright (c) 2022, DCKY and contributors
// For license information, please see license.txt

frappe.ui.form.on('Frepple Integration', {
	post:function(frm){
		frm.trigger('pr');
	},

	get:function(frm){
		console.log("Trigger get request")
		frm.trigger('gr');
	},


	gr:function(frm){
		console.log("GET request is triggered")
		frm.call({
			method:"get_demand",
			doc: frm.doc,
			// method:"make_request",
			callback:function(r){
				console.log(r.message)
			}
		});
	},

	pr:function(frm){
		frm.call({
			// method:"get_manufacturingorder",
			// method:"post_location",
			method:"test",
			// method:"post_demand",
			doc: frm.doc,
			// method:"run_plan",
			callback: function(r) {
				console.log(r.message)
			}
		});
	}

	

})
