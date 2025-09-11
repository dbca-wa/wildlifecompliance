<template>
    <div class="container" id="internalOrgInfo">
    <!-- <div class="row"> -->
    <!-- <div class="col-md-10 col-md-offset-1"> -->
        <div class="row">
            <div class="col-md-9">
                <h3>{{ org.name }} - {{org.abn}}</h3>
            </div>
        </div>        
            <div class="col-md-4">
                <CommsLogs :comms_url="comms_url" :logs_url="logs_url" comms_add_url="test"/>
            </div>
            <div class="col-md-8">
                <ul class="nav nav-pills mb-3" id="pills-tab" role="tablist">
                    <li class="nav-item">
                        <a class="nav-link active" id="pills-details-tab" data-toggle="pill" href="#pills-details" role="tab" aria-controls="pills-details" aria-selected="true">
                            Details
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" id="pills-licensing-tab" data-toggle="pill" href="#pills-licensing" role="tab" aria-controls="pills-licensing" aria-selected="false">
                            Licensing
                        </a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" id="pills-compliance-tab" data-toggle="pill" href="#pills-compliance" role="tab" aria-controls="pills-compliance" aria-selected="false">
                            Compliance
                        </a>
                    </li>
                </ul>
                <div class="tab-content">
                    <div class="tab-pane fade" id="pills-details" role="tabpanel" aria-labelledby="pills-details-tab">
                        <div class="row">
                            <div class="col-sm-12">
                                <FormSection
                                    :form-collapse="false"
                                    label="Organisation Details"
                                >
                                    <div class="panel panel-default">
                                      <form class="form-horizontal" name="personal_form" method="post">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Name</label>
                                            <div class="col-sm-6">
                                                <input type="text" class="form-control" name="first_name" placeholder="" v-model="org.name">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >ABN</label>
                                            <div class="col-sm-6">
                                                <input type="text" disabled class="form-control" name="last_name" placeholder="" v-model="org.abn">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <div class="col-sm-12">
                                                <button v-if="!updatingDetails" class="float-end btn btn-primary" @click.prevent="updateDetails()">Update</button>
                                                <button v-else disabled class="float-end btn btn-primary"><i class="fa fa-spin fa-spinner"></i>&nbsp;Updating</button>
                                            </div>
                                          </div>
                                       </form>
                                  </div>
                                </FormSection>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-sm-12">
                                <FormSection
                                    :form-collapse="false"
                                    label="Address Details"
                                >
                                    <div class="panel panel-default">
                                      <form class="form-horizontal" action="index.html" method="post">
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">Street</label>
                                            <div class="col-sm-6">
                                                <input type="text" class="form-control" name="street" placeholder="" v-model="org.address.line1">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                                            <div class="col-sm-6">
                                                <input type="text" class="form-control" name="surburb" placeholder="" v-model="org.address.locality">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label">State</label>
                                            <div class="col-sm-2">
                                                <input type="text" class="form-control" name="country" placeholder="" v-model="org.address.state">
                                            </div>
                                            <label for="" class="col-sm-2 control-label">Postcode</label>
                                            <div class="col-sm-2">
                                                <input type="text" class="form-control" name="postcode" placeholder="" v-model="org.address.postcode">
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <label for="" class="col-sm-3 control-label" >Country</label>
                                            <div class="col-sm-4">
                                                <select class="form-control" name="country" v-model="org.address.country">
                                                    <option v-for="c in countries" :value="c.code" v-bind:key="`code_${c.code}`">{{ c.name }}</option>
                                                </select>
                                            </div>
                                          </div>
                                          <div class="form-group">
                                            <div class="col-sm-12">
                                                <button v-if="!updatingAddress" class="float-end btn btn-primary" @click.prevent="updateAddress()">Update</button>
                                                <button v-else disabled class="float-end btn btn-primary"><i class="fa fa-spin fa-spinner"></i>&nbsp;Updating</button>
                                            </div>
                                          </div>
                                       </form>
                                    </div>
                                </FormSection>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-sm-12">
                                <FormSection
                                    :form-collapse="false"
                                    label="Contact Details"
                                >
                                    <div class="panel panel-default">
                                        <form class="form-horizontal" action="index.html" method="post">
                                            <div class="col-sm-12">
                                                <button @click.prevent="addContact()" style="margin-bottom:10px;" class="btn btn-primary float-end">Add Contact</button>
                                            </div>
                                            <datatable ref="contacts_datatable" id="organisation_contacts_datatable" :dtOptions="contacts_options" :dtHeaders="contacts_headers"/>
                                        </form>
                                    </div>
                                </FormSection>
                            </div>
                        </div>
                        <div class="row">
                            <div class="col-sm-12">
                                <FormSection
                                    :form-collapse="false"
                                    label="Linked Persons"
                                    subtitle="Manage the user accounts linked to the organisation"
                                >
                                    <div class="panel panel-default">
                                    <div class ="row">
                                        <form class="form-horizontal" action="index.html" method="post">
                                            <div class="col-sm-6">
                                                <div class="form-group">
                                                    <label for="" class="col-sm-6 control-label"> Organisation User Pin Code 1:</label>
                                                    <div class="col-sm-6">
                                                        <label class="control-label">{{org.pins ? org.pins.three : ' '}}</label>
                                                    </div>
                                                </div>
                                                <div class="form-group">
                                                    <label for="" class="col-sm-6 control-label" >Organisation User Pin Code 2:</label>
                                                    <div class="col-sm-6">
                                                        <label class="control-label">{{org.pins ? org.pins.four : ' '}}</label>
                                                    </div>
                                                </div>
                                             </div>
                                             <div class="col-sm-6">
                                                <div class="form-group">
                                                    <label for="" class="col-sm-6 control-label"> Organisation Administrator Pin Code 1:</label>
                                                    <div class="col-sm-6">
                                                        <label class="control-label">{{org.pins ? org.pins.one : ' '}}</label>
                                                    </div>
                                                </div>
                                                <div class="form-group">
                                                    <label for="" class="col-sm-6 control-label" >Organisation Administrator Pin Code 2:</label>
                                                    <div class="col-sm-6">
                                                        <label class="control-label">{{org.pins ? org.pins.two : ' '}}</label>
                                                    </div>
                                                </div>
                                            </div>
                                        </form>
                                    </div>
                                    <div class="row">
                                        <div class="col-sm-8">
                                            <div class="row">
                                                <div class="col-sm-12 top-buffer-s">
                                                    <strong>Persons linked to the organisation are controlled by the organisation. The Department cannot manage this list of people.</strong>
                                                </div>
                                            </div> 
                                        </div>
                                    </div>
                                    <div>
                                        <datatable ref="contacts_datatable_user" id="organisation_contacts_datatable_ref" :dtOptions="contacts_options_ref" :dtHeaders="contacts_headers_ref" />
                                    </div>
                                    </div>
                                </FormSection>
                            </div>
                        </div>
                    </div> 
                    <!--div :id="oTab" class="tab-pane fade"-->
                    <div class="tab-pane fade" id="pills-licensing" role="tabpanel" aria-labelledby="pills-licensing-tab">
                        <ApplicationDashTable ref="applications_table" level='internal' :url='applications_url'/>
                        <LicenceDashTable ref="licences_table" level='internal' :url='licences_url'/>
                        <ReturnDashTable ref="returns_table" level='internal' :url='returns_url'/>
                    </div>
                    <div class="tab-pane fade" id="pills-compliance" role="tabpanel" aria-labelledby="pills-compliance-tab">
                        <SanctionOutcomePersonOrgDashTable 
                        v-if="org.id"
                        ref="sanction_outcome_person_org_table" 
                        level='internal' 
                        :entity_id='org.id'
                        entity_type='org'
                        />
                        <IntelligenceInformation
                        v-if="org.id"
                        ref="intelligence_information" 
                        :entity_id='org.id'
                        entity_type='org'
                        />
                    </div>
                </div>
            </div>
        <!-- </div>
        </div> -->
        <!-- </div> -->
        <AddContact ref="add_contact" :org_id="org.id" />
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
//import $ from 'jquery'
import Vue from 'vue'
import { api_endpoints, helpers, fetch_util } from '@/utils/hooks'
import datatable from '@vue-utils/datatable.vue'
import AddContact from '@common-components/add_contact.vue'
import ApplicationDashTable from '@common-components/applications_dashboard.vue'
import LicenceDashTable from '@common-components/licences_dashboard.vue'
import ReturnDashTable from '@common-components/returns_dashboard.vue'
import SanctionOutcomePersonOrgDashTable from '@common-components/sanction_outcomes_person_org_dashboard.vue'
import IntelligenceInformation from '@common-components/intelligence_information.vue'
import CommsLogs from '@common-components/comms_logs.vue'
import utils from '../utils'
import api from '../api'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'Organisation',
    data () {
        let vm = this;
        return {
            adBody: 'adBody'+uuid(),
            aBody: 'aBody'+uuid(),
            pdBody: 'pdBody'+uuid(),
            pBody: 'pBody'+uuid(),
            cdBody: 'cdBody'+uuid(),
            cBody: 'cBody'+uuid(),
            oBody: 'oBody'+uuid(),
            dTab: 'dTab'+uuid(),
            oTab: 'oTab'+uuid(),
            idBody: 'idBody'+uuid(),
            org: {
                address: {}
            },
            myorgperms: null,
            loading: [],
            countries: [],
            updatingDetails: false,
            updatingAddress: false,
            updatingContact: false,
            uploadingID: false,
            uploadedID: null,
            empty_list: '/api/empty_list',
            logsTable: null,
            DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
            activate_tables: false,
            comms_url: helpers.add_endpoint_json(api_endpoints.organisations,vm.$route.params.org_id+'/comms_log'),
            logs_url: helpers.add_endpoint_json(api_endpoints.organisations,vm.$route.params.org_id+'/action_log'),
            contacts_headers:["Name","Phone","Mobile","Fax","Email","Action"],
            contacts_headers_ref:["Name","Role","Email","Status"],
            applications_url: api_endpoints.applications_paginated+'internal_datatable_list?org_id='+vm.$route.params.org_id,
            licences_url: api_endpoints.licences_paginated+'internal_datatable_list?org_id='+vm.$route.params.org_id,
            returns_url: api_endpoints.returns_paginated+'user_datatable_list?org_id='+vm.$route.params.org_id,
            contacts_options:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": helpers.add_endpoint_json(api_endpoints.organisations,vm.$route.params.org_id+'/contacts'),
                    "dataSrc": ''
                },
                columns: [
                    {
                        data:'last_name',
                        mRender:function (data,type,full) {
                            return full.first_name + " " + full.last_name;
                        }
                    },
                    {data:'phone_number'},
                    {data:'mobile_number'},
                    {data:'fax_number'},
                    {data:'email'},
                    {
                        data:'user_status',
                        mRender:function (data,type,full) {
                            let links = '';
                            let name = full.first_name + ' ' + full.last_name;
                            if (full.user_status.id == 'draft' ){
                                links +=  `<a data-email='${full.email}' data-name='${name}' data-id='${full.id}' class="remove-contact">Remove</a><br/>`;
                            }
                            return links;
                        }
                    }
                ],
                processing: true
            },

            contacts_options_ref:{
               language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": helpers.add_endpoint_json(api_endpoints.organisations,vm.$route.params.org_id+'/contacts_exclude'),
                    "dataSrc": ''
                },
                columns: [
                    {
                        data:'last_name',
                        mRender:function (data,type,full) {
                            return full.first_name + " " + full.last_name;
                        }
                    },
                    {
                        data:'user_role',
                        mRender:function (data,type,full) {
                            return full.user_role.name;
                        }
                    },
                    {data:'email'},
                    {
                        data:'user_status',
                        mRender:function (data,type,full) {
                            return full.user_status.name;
                        }
                    },
                  ],
                  processing: true
                  
                
            }



        }
    },
    components: {
        FormSection,
        datatable,
        ApplicationDashTable,
        LicenceDashTable,
        ReturnDashTable,
        SanctionOutcomePersonOrgDashTable,
        AddContact,
        CommsLogs,
        IntelligenceInformation,
    },
    computed: {
        isLoading: function () {
          return this.loading.length == 0;
        },
        uploadedIDFileName: function() {
            return this.uploadedID != null ? this.uploadedID.name: '';
        },
    },
    beforeRouteEnter: function(to, from, next){
        let initialisers = [
            utils.fetchCountries(),
            utils.fetchOrganisation(to.params.org_id),
            utils.fetchOrganisationPermissions(to.params.org_id)
        ]
        Promise.all(initialisers).then(data => {
            next(vm => {
                vm.countries = data[0];
                vm.org = data[1];
                vm.myorgperms = data[2];
                vm.org.address = vm.org.address != null ? vm.org.address : {};
                vm.org.pins = vm.org.pins != null ? vm.org.pins : {};
            });
        });
    },
    beforeRouteUpdate: function(to, from, next){
        let initialisers = [
            utils.fetchOrganisation(to.params.org_id),
            utils.fetchOrganisationPermissions(to.params.org_id)
        ]
        Promise.all(initialisers).then(data => {
            next(vm => {
                vm.org = data[0];
                vm.myorgperms = data[1];
                vm.org.address = vm.org.address != null ? vm.org.address : {};
                vm.org.pins = vm.org.pins != null ? vm.org.pins : {};
            });
        });
    },
    methods: {
        /*set_tabs:function(){
            let vm = this;
            $('#pills-tab a[href="#pills-details"]').tab('show');
        },*/

        addContact: function(){
            this.$refs.add_contact.isModalOpen = true;
        },
        eventListeners: function(){
            let vm = this;
            vm.$refs.contacts_datatable.vmDataTable.on('click','.remove-contact',(e) => {
                e.preventDefault();

                let name = $(e.target).data('name');
                let email = $(e.target).data('email');
                let id = $(e.target).data('id');
                swal.fire({
                    title: "Delete Contact",
                    text: "Are you sure you want to remove "+ name + "("+ email + ") as a contact  ?",
                    type: "error",
                    showCancelButton: true,
                    confirmButtonText: 'Accept'
                }).then((result) => {
                    if (result) {
                        vm.deleteContact(id);
                    }
                },(error) => {
                });
            });
            // Fix the table responsiveness when tab is shown
            $('a[href="#'+vm.oTab+'"]').on('shown.bs.tab', function (e) {
                vm.$refs.applications_table.$refs.application_datatable.vmDataTable.columns.adjust().responsive.recalc();
                // vm.$refs.licences_table.$refs.application_datatable.vmDataTable.columns.adjust().responsive.recalc();
                // vm.$refs.returns_table.$refs.application_datatable.vmDataTable.columns.adjust().responsive.recalc();
            });
        },
        updateDetails: function() {
            let vm = this;
            vm.updatingDetails = true;
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,(vm.org.id+'/update_details')), {method:'POST', body:JSON.stringify(vm.org)},{
                emulateJSON:true
            })
            request.then((response) => {
                vm.updatingDetails = false;
                vm.org = response;
                if (vm.org.address == null){ vm.org.address = {}; }
                swal.fire(
                    'Saved',
                    'Organisation details have been saved',
                    'success'
                )
            }, (error) => {
                console.log(error);
                vm.updatingDetails = false;
            });
        },
        addedContact: function() {
            let vm = this;
            swal.fire(
                'Added',
                'The contact has been successfully added.',
                'success'
            )
            vm.$refs.contacts_datatable.vmDataTable.ajax.reload();
        },
        deleteContact: function(id){
            let vm = this;
            
            let request = fetch_util.fetchUrl(
                helpers.add_endpoint_json(api_endpoints.organisation_contacts,id), {method:"DELETE"},
                {
                    emulateJSON:true
                })
            request.then((response) => {
                swal.fire(
                    'Contact Deleted', 
                    'The contact was successfully deleted',
                    'success'
                )
                vm.$refs.contacts_datatable.vmDataTable.ajax.reload();
            }, (error) => {
                console.log(error);
                swal.fire(
                    'Contact Deleted', 
                    'The contact could not be deleted because of the following error '+error,
                    'error'
                )
            });
        },
        updateAddress: function() {
            let vm = this;
            vm.updatingAddress = true;
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,(vm.org.id+'/update_address')), {method:'POST', body:JSON.stringify(vm.org.address)},{
                emulateJSON:true
            })
            request.then((response) => {
                vm.updatingAddress = false;
                vm.org = response;
                swal.fire(
                    'Saved',
                    'Address details have been saved',
                    'success'
                )
                if (vm.org.address == null){ vm.org.address = {}; }
            }, (error) => {
                console.log(error);
                vm.updatingAddress = false;
            });
        },
        readFileID: function() {
            let vm = this;
            let _file = null;
            var input = $(vm.$refs.uploadedID)[0];
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(input.files[0]);
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            vm.uploadedID = _file;
        },
        uploadID: function() {
            let vm = this;
            vm.uploadingID = true;
            let data = new FormData();
            data.append('identification', vm.uploadedID);
            if (vm.uploadedID == null){
                vm.uploadingID = false;
                swal.fire({
                        title: 'Upload ID',
                        html: 'Please select a file to upload.',
                        type: 'error'
                });
            } else {
                let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisations,(vm.org.id+'/upload_id')),{method:'POST', body:JSON.stringify(data)},{
                    emulateJSON:true
                })
                request.then((response) => {
                    vm.uploadingID = false;
                    vm.uploadedID = null;
                    swal.fire({
                        title: 'Upload ID',
                        html: 'The organisation ID has been successfully uploaded.',
                        type: 'success',
                    }).then(() => {
                        window.location.reload(true);
                    });
                }, (error) => {
                    console.log(error);
                    vm.uploadingID = false;
                    let error_msg = '<br/>';
                    for (var key in error.body) {
                        error_msg += key + ': ' + error.body[key] + '<br/>';
                    }
                    swal.fire({
                        title: 'Upload ID',
                        html: 'There was an error uploading the organisation ID.<br/>' + error_msg,
                        type: 'error'
                    });
                });
            }
        },
    },
    mounted: function(){
        let vm =this;
        //this.set_tabs();
        this.personal_form = document.forms.personal_form;
        this.eventListeners();
    },
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.top-buffer-s {
    margin-top: 10px;
}
.actionBtn {
    cursor: pointer;
}
.hidePopover {
    display: none;
}
#main-column {
  padding-left: 2%;
  padding-right: 0;
  margin-bottom: 50px;
}
</style>
