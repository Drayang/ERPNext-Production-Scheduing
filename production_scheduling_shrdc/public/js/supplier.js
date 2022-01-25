frappe.ui.form.on("Supplier",{ 
    
    after_save: function(frm) {
        frm.trigger('post_supplier');
    },
    
    post_supplier: function(frm){
                //frappe.msgprint("Please do not select the past date");
        // frappe.msgprint({
        //     title: __('Note'),
        //     indicator: 'green',
        //     message: __('Data have been exported to Frepple.')
        // });
        frappe.call({ // call check_duplicate_wo to remove any work order that ady exist to prevent duplicate production plan for the same wo
            method:"production_scheduling_shrdc.production_scheduling_shrdc.doctype.frepple_integration.frepple_integration.post_supplier",
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