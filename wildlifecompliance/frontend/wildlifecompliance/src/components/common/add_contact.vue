<template lang="html">
    <div id="change-contact">
        <modal :modelValue="modelValue"
            @update:modelValue="$emit('update:modelValue', $event)"
            ok-text="Add" @submit="ok()" @close="cancel()" title="Add Contact" size="lg">
            
            <form class="form-horizontal" name="addContactForm">
                <div class="row">
                    <alert v-if="showError" type="danger"><strong>{{errorString}}</strong></alert>
                    <div class="col-lg-12">
                        <div class="row">
                            <div class="form-group">
                                <label class="col-md-3 control-label float-start"  for="Name">Given Name(s): </label>
                                <div class="col-md-9">
                                    <input type="text" class="form-control" name="name" v-model="contact.first_name" />
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="form-group">
                                <label class="col-md-3 control-label float-start"  for="Name">Surname: </label>
                                <div class="col-md-9">
                                    <input type="text" class="form-control" name="name" v-model="contact.last_name" />
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="form-group">
                                <label class="col-md-3 control-label float-start"  for="Phone">Phone: </label>
                                <div class="col-md-9">
                                    <input type="text" class="form-control" name="phone" v-model="contact.phone_number" />
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="form-group">
                                <label class="col-md-3 control-label float-start"  for="Mobile">Mobile: </label>
                                <div class="col-md-9">
                                    <input type="text" class="form-control" name="mobile" v-model="contact.mobile_number" />
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="form-group">
                                <label class="col-md-3 control-label float-start"  for="Fax">Fax: </label>
                                <div class="col-md-9">
                                    <input type="text" class="form-control" name="fax" v-model="contact.fax_number" />
                                </div>
                            </div>
                        </div>
                        <div class="row">
                            <div class="form-group">
                                <label class="col-md-3 control-label float-start"  for="Email">Email: </label>
                                <div class="col-md-9">
                                    <input type="text" class="form-control" name="email" v-model="contact.email" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </form>
            <template #footer>
                <button type="button" v-if="addingContact" disabled class="btn btn-secondary"><i class="fa fa-spinner fa-spin"></i> Adding</button>
                <button type="button" v-else class="btn btn-primary" @click="ok">Add</button>
                <button type="button" class="btn btn-secondary" @click="close">Cancel</button>
            </template>
        </modal>
    </div>
</template>

<script>
import modal from '@vue-utils/bootstrap5-modal.vue'
import alert from '@vue-utils/alert.vue'
import {helpers,api_endpoints,fetch_util} from "@/utils/hooks.js"
export default {
    name:'Add-Organisation-Contact',
    components:{
        modal,
        alert
    },
    props:{
            modelValue: {
                type: Boolean,
                required: true,
            },
            org_id:{
                type:Number,
            },
    },
    emits: ['update:modelValue'],
    data:function () {
        let vm = this;
        return {
            addingContact: false,
            form:null,
            contact: {},
            errors: false,
            errorString: '',
            successString: '',
            success:false,
        }
    },
    computed: {
        showError: function() {
            var vm = this;
            return vm.errors;
        }
    },
    methods:{
        ok:function () {
            let vm =this;
            if($(vm.form).valid()){
                vm.sendData();
            }
        },
        close:function () {
            this.$emit('update:modelValue', false); 
            this.contact = {};
            this.errors = false;
            this.form.reset();
        },
        fetchContact: function(id){
            let vm = this;
            let request = fetch_util.fetchUrl(api_endpoints.contact(id))
            request.then((response) => {
                vm.contact = response;
            }).catch((error) => {
                console.log(error);
            });
        },
        sendData:function(){
            let vm = this;
            vm.errors = false;
            if (vm.contact.id){
                vm.addingContact = true;
                let contact = vm.contact;
                let request = fetch_util.fetchUrl(api_endpoints.organisation_contacts(contact.id),
                    {method:"PUT",body:JSON.stringify(contact)},{
                        emulateJSON:true,
                    })
                request.then((response)=>{
                        vm.addingContact = false;
                        vm.close();
                    },(error)=>{
                        console.log(error);
                        vm.addingContact = false;
                        vm.errors = true;
                        vm.errorString = helpers.apiVueResourceError(error);
                    });
            } else {
                vm.addingContact = true;
                let contact = vm.contact;
                contact.organisation = vm.org_id;
                let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,vm.org_id+'/add_nonuser_contact'),
                    {method:'POST', body:JSON.stringify(contact)},{
                        emulateJSON:true,
                    })
                request.then((response)=>{
                        vm.addingContact = false;
                        vm.close();
                        vm.$parent.addedContact();
                    },(error)=>{
                        console.log(error);
                        vm.addingContact = false;
                        vm.errors = true;
                        vm.errorString = helpers.apiVueResourceError(error);
                    });
                
            }
        },
        addFormValidations: function() {
            let vm = this;
            $(vm.form).validate({
                rules: {
                    arrival:"required",
                    departure:"required",
                    campground:"required",
                    campsite:{
                        required: {
                            depends: function(el){
                                return vm.campsites.length > 0;
                            }
                        }
                    }
                },
                messages: {
                    arrival:"field is required",
                    departure:"field is required",
                    campground:"field is required",
                    campsite:"field is required"
                },
                showErrors: function(errorMap, errorList) {
                    $.each(this.validElements(), function(index, element) {
                        var $element = $(element);
                        $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
                    });
                    // destroy tooltips on valid elements
                    $("." + this.settings.validClass).tooltip("destroy");
                    // add or update tooltips
                    for (var i = 0; i < errorList.length; i++) {
                        var error = errorList[i];
                        $(error.element)
                            .tooltip({
                                trigger: "focus"
                            })
                            .attr("data-original-title", error.message)
                            .parents('.form-group').addClass('has-error');
                    }
                }
            });
       },
       eventListerners:function () {
           let vm = this;
       }
   },
   watch: {
        modelValue(newValue) {
            if (newValue === true) {
                this.$nextTick(() => {
                    this.form = document.forms.addContactForm;
                    this.addFormValidations();
                });
            }
        }
    },
}
</script>

<style lang="css">
.modal-header {
    display: block;
}
</style>
