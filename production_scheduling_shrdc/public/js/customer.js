frappe.ui.form.on("Customer",{ 
    
    after_save: function(frm) {
        frm.trigger('post_customer');
    },
    
    post_customer: function(frm){
        frappe.call({ // call check_duplicate_wo to remove any work order that ady exist to prevent duplicate production plan for the same wo
            method:"production_scheduling_shrdc.production_scheduling_shrdc.doctype.frepple_integration.frepple_integration.post_customer",
            args: {
                //Argument we defined in method : argument to pass to
                doc:frm.doc,
            },
            callback: function(r) {
                console.log(r.message)
            }
        })
    }
})