frappe.ui.form.on("Workstation",{ 
    after_save: function(frm) {
        frm.trigger('post_workstation');
    },
    
    post_workstation: function(frm){
        frappe.call({ // call check_duplicate_wo to remove any work order that ady exist to prevent duplicate production plan for the same wo
            method:"production_scheduling_shrdc.production_scheduling_shrdc.doctype.frepple_integration.frepple_integration.post_workstation",
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
