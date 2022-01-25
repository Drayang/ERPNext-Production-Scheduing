frappe.ui.form.on("Employee Skill Map",{ 
    after_save: function(frm) {
        frm.trigger('post_resourceskill');
    },
    
    post_resourceskill: function(frm){
        frappe.msgprint({
            title: __('Note'),
            indicator: 'green',
            message: __('Data have been exported to Frepple.')
        });
        frappe.call({ // call check_duplicate_wo to remove any work order that ady exist to prevent duplicate production plan for the same wo
            method:"production_scheduling_shrdc.production_scheduling_shrdc.doctype.frepple_integration.frepple_integration.post_resourceskill",
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
