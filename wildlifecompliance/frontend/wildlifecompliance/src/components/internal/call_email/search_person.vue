<template lang="html">
    <div class="col-sm-12 form-group">
        <div class="row" >
            <label class="col-sm-3 control-label">Search Person</label>
            <div class="col-sm-6">
                <PersonSearch :readonly="!isEditable" ref="person_search" elementId="search_caller" classNames="col-sm-5 form-control" @person-selected="personSelected" />
            </div>
            <div class="col-sm-3">
                <input :readonly="!isEditable" type="button" class="float-end btn btn-primary" value="Create New Person" @click.prevent="createNewPerson()" />
            </div>
        </div>
        <div class="col-md-12">
            <ul class="nav nav-pills">
                <li class="nav-item active"><a data-toggle="tab" :href="'#'+dTab">Details</a></li>
                <li class="nav-item"><a data-toggle="tab" :href="'#'+oTab">Licensing</a></li>
            </ul>
            <div class="tab-content">
                <div :id="dTab" class="tab-pane fade in active">
                    <div class="row">
                        <div class="col-sm-12">
                            <FormSection
                                :form-collapse="false"
                                label="Personal Details"
                            >
                                <div class="panel panel-default">
                                    <div v-if="objectAlert" class="alert alert-danger">
                                        <p>test alert</p>
                                    </div>
                                    <form class="form-horizontal" name="personal_form" method="post">
                                        <div class="form-group" v-bind:class="{ 'has-error': errorGivenName }">
                                            <label for="" class="col-sm-3 control-label">Given Name(s)</label>
                                            <div class="col-sm-6">
                                                <div v-if="call_email.email_user">
                                                    <input :readonly="!isEditable" type="text" class="form-control" name="first_name" placeholder="" v-model="call_email.email_user.first_name" v-bind:key="call_email.email_user.id">
                                                </div>
                                            </div>
                                        </div>
                                        <div class="form-group" v-bind:class="{ 'has-error': errorLastName }">
                                            <label for="" class="col-sm-3 control-label">Last Name</label>
                                            <div class="col-sm-6">
                                                <div v-if="call_email.email_user">
                                                    <input :readonly="!isEditable" type="text" class="form-control" name="last_name" placeholder="" v-model="call_email.email_user.last_name" v-bind:key="call_email.email_user.id">
                                                </div>
                                            </div>
                                        </div>
                                        <div class="form-group" v-bind:class="{ 'has-error': errorDob }">
                                            <label for="" class="col-sm-3 control-label" >Date of Birth</label>
                                            <div class="col-sm-6">
                                                <div v-if="call_email.email_user">
                                                    <input :readonly="!isEditable" type="date" class="form-control" name="dob" placeholder="" v-model="call_email.email_user.dob" v-bind:key="call_email.email_user.id">
                                                </div>
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
                                <div v-if="loading.length == 0" class="panel panel-default">
                                    <form class="form-horizontal" action="index.html" method="post">
                                        <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Street</label>
                                        <div class="col-sm-6">
                                            <div v-if="call_email.email_user"><div v-if="call_email.email_user.residential_address">
                                                <input :readonly="!isEditable" type="text" class="form-control" name="street" placeholder="" v-model="call_email.email_user.residential_address.line1" v-bind:key="call_email.email_user.residential_address.id">
                                            </div></div>
                                        </div>
                                        </div>
                                    <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                                        <div class="col-sm-6">
                                            <div v-if="call_email.email_user"><div v-if="call_email.email_user.residential_address">
                                                <input :readonly="!isEditable" type="text" class="form-control" name="surburb" placeholder="" v-model="call_email.email_user.residential_address.locality" v-bind:key="call_email.email_user.residential_address.id">
                                            </div></div>
                                        </div>
                                        </div>
                                        <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">State</label>
                                        <div class="col-sm-2">
                                            <div v-if="call_email.email_user"><div v-if="call_email.email_user.residential_address">
                                                <input :readonly="!isEditable" type="text" class="form-control" name="country" placeholder="" v-model="call_email.email_user.residential_address.state" v-bind:key="call_email.email_user.residential_address.id">
                                            </div></div>
                                        </div>
                                        <label for="" class="col-sm-2 control-label">Postcode</label>
                                        <div class="col-sm-2">
                                            <div v-if="call_email.email_user"><div v-if="call_email.email_user.residential_address">
                                                <input :readonly="!isEditable" type="text" class="form-control" name="postcode" placeholder="" v-model="call_email.email_user.residential_address.postcode" v-bind:key="call_email.email_user.residential_address.id">
                                            </div></div>
                                        </div>
                                        </div>
                                        <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Country</label>
                                        <div class="col-sm-4">
                                            <div v-if="call_email.email_user"><div v-if="call_email.email_user.residential_address">
                                                <select :disabled="!isEditable" class="form-control" name="country" v-model="call_email.email_user.residential_address.country" v-bind:key="call_email.email_user.residential_address.id">
                                                    <option v-for="c in countries" :value="c.code">{{ c.name }}</option>
                                                </select>
                                            </div></div>
                                        </div>
                                        </div>
                                        <!-- <div class="form-group">
                                        <div class="col-sm-12">
                                            <button v-if="!updatingAddress" class="float-end btn btn-primary" @click.prevent="updateAddress()">Update</button>
                                            <button v-else disabled class="float-end btn btn-primary"><i class="fa fa-spin fa-spinner"></i>&nbsp;Updating</button>
                                        </div>
                                        </div>  -->
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
                                        <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Phone</label>
                                        <div class="col-sm-6">
                                            <div v-if="call_email.email_user">
                                                <input :readonly="!isEditable" type="text" class="form-control" name="phone" placeholder="" v-model="call_email.email_user.phone_number" v-bind:key="call_email.email_user.id">
                                            </div>
                                        </div>
                                        </div>
                                        <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Mobile</label>
                                        <div class="col-sm-6">
                                            <div v-if="call_email.email_user">
                                                <input :readonly="!isEditable" type="text" class="form-control" name="mobile" placeholder="" v-model="call_email.email_user.mobile_number" v-bind:key="call_email.email_user.id">
                                            </div>
                                        </div>
                                        </div>
                                        <div class="form-group">
                                        <label for="" class="col-sm-3 control-label" >Email</label>
                                        <div class="col-sm-6">
                                            <div v-if="call_email.email_user">
                                                <input :readonly="!isEditable" type="email" class="form-control" name="email" placeholder="" v-model="call_email.email_user.email" v-bind:key="call_email.email_user.id"> </div>
                                            </div>
                                        </div>
                                        <!-- <div class="form-group">
                                        <div class="col-sm-12">
                                            <button v-if="!updatingContact" class="float-end btn btn-primary" @click.prevent="updateContact()">Update</button>
                                            <button v-else disabled class="float-end btn btn-primary"><i class="fa fa-spin fa-spinner"></i>&nbsp;Updating</button>
                                        </div>
                                        </div> -->
                                    </form>
                                </div>
                            </FormSection>
                        </div>
                    </div>
                    <div class="row" v-if="isEditable">
                        <div class="col-sm-12">
                            <button v-if="!updatingContact" class="float-end btn btn-primary" @click.prevent="save">Update</button>
                            <button v-else disabled class="float-end btn btn-primary"><i class="fa fa-spin fa-spinner"></i>&nbsp;Updating</button>
                        </div>
                    </div>
                </div>
                <div :id="oTab" class="tab-pane fade">
                    <div v-if="call_email.email_user">
                        <ApplicationDashTable ref="applications_table" level='internal' :url='applications_url' v-bind:key="call_email.email_user.id"/>
                    </div>
                    <div v-if="call_email.email_user">
                        <LicenceDashTable ref="licences_table" level='internal' :url='licences_url' v-bind:key="call_email.email_user.id"/>
                    </div>
                    <div v-if="call_email.email_user">
                        <ReturnDashTable ref="returns_table" level='internal' :url='returns_url' v-bind:key="call_email.email_user.id"/>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
        
<script>
import { v4 as uuid } from 'uuid';
import Awesomplete from 'awesomplete';
import { api_endpoints, helpers, fetch_util } from '@/utils/hooks'
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import datatable from '@vue-utils/datatable.vue'
import ApplicationDashTable from '@common-components/applications_dashboard.vue'
import LicenceDashTable from '@common-components/licences_dashboard.vue'
import ReturnDashTable from '@common-components/returns_dashboard.vue'
import PersonSearch from "@/components/common/search_person_or_organisation.vue";

import 'awesomplete/awesomplete.css';
import utils from '../utils'

import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: "search-person",
    data: function(){
        let vm = this;
        vm.max_items = 10;
        vm.ajax_for_person_search = null;

        return {
            awe: null,
            suggest_list: [],
            adBody: 'adBody'+uuid(),
            pdBody: 'pdBody'+uuid(),
            cdBody: 'cdBody'+uuid(),
            odBody: 'odBody'+uuid(),
            idBody: 'idBody'+uuid(),
            dTab: 'dTab'+uuid(),
            oTab: 'oTab'+uuid(),
            user: {
                residential_address: {},
                wildlifecompliance_organisations: []
            },
            loading: [],
            countries: [],
            updatingAddress: false,
            updatingPersonal: false,
            updatingContact: false,
            errorGivenName: false,
            errorLastName: false,
            errorDob: false,
            objectAlert: false,

            //forDemo: false,
        }
    },
    components: {
        FormSection,
        datatable,
        ApplicationDashTable,
        LicenceDashTable,
        ReturnDashTable,
        //CommsLogs
        PersonSearch
    },
    computed: {
        ...mapGetters('callemailStore', {
            call_email: "call_email",
        }),
        ...mapGetters({
            // renderer_form_data: 'renderer_form_data',
            current_user: 'current_user',
        }),
        //isReadonly: function() {
          //  if (this.call_email.status && this.call_email.status.id === 'draft') {
            //    return false;
            //} else {
            //    return true;
           // }
        //},
        isEditable: function() {
            //if (!this.forDemo){
             //   return true;
            //}

            //if (this.call_email.status && this.call_email.status.id === 'open' && this.current_user.is_officer) {
              //  return true;
            //} else {
              //  return false;
            //}
            return this.call_email.can_user_search_person;
        },
        applications_url: function(){
            if (this.call_email.email_user && this.call_email.email_user.id){
                return api_endpoints.applications_paginated+'internal_datatable_list?user_id=' + this.call_email.email_user.id;
            }
            return api_endpoints.applications_paginated+'internal_datatable_list';
        },
        licences_url: function(){
            if (this.call_email.email_user && this.call_email.email_user.id){
                return api_endpoints.licences_paginated+'internal_datatable_list?user_id=' + this.call_email.email_user.id;
            }
            return api_endpoints.licences_paginated+'internal_datatable_list';
        },
        returns_url: function(){
            console.log('returns_url')
            if (this.call_email.email_user && this.call_email.email_user.id){
                return api_endpoints.returns_paginated+'user_datatable_list?user_id=' + this.call_email.email_user.id;
            }
            return api_endpoints.returns_paginated+'user_datatable_list';
        }
    },
    mounted: function(){
        this.$nextTick(function() {
            // this.initAwesomplete();
            this.loadCountries();
        });
    },
    methods: {
        ...mapActions('callemailStore', {
            setEmailUserEmpty: "setEmailUserEmpty",
            saveCallEmail: 'saveCallEmail',
            saveCallEmailPerson: 'saveCallEmailPerson',
        }),
        personSelected(para){
            this.loadEmailUser(para.id);
        },
        save: async function() {
            await this.saveCallEmailPerson();
        },
        createNewPerson: function() {
            let vm = this;
            vm.setEmailUserEmpty();
            vm.$refs.person_search.clearInput();
        },
        updateContact: function() {
            let vm = this;
            vm.updatingContact = true;
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.users,(vm.call_email.email_user.id+'/update_contact')), {method:'POST', body:JSON.stringify(vm.call_email.email_user)},{
                emulateJSON:true
            })
            request.then((response) => {
                vm.updatingContact = false;
                // vm.user = response;
                if (vm.call_email.email_user.residential_address == null){ vm.call_email.email_user.residential_address = {}; }
                swal.fire({
                    title: 'Update Contact Details',
                    html: 'User contact details has been successfully updated.',
                    type: 'success',
                })
            }, (error) => {
                vm.updatingContact = false;
                let error_msg = '<br/>';
                for (var key in error.body) {
                    error_msg += key + ': ' + error.body[key] + '<br/>';
                }
                swal.fire({
                    title: 'Update Contact Details',
                    html: 'There was an error updating the user contact details.<br/>' + error_msg,
                    type: 'error'
                })
            });
        },
        updateAddress: function() {
            let vm = this;
            vm.updatingAddress = true;
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.users,(vm.call_email.email_user.id+'/update_address')), {method:'POST', body:JSON.stringify(vm.call_email.email_user.residential_address)},{
                emulateJSON:true
            })
            request.then((response) => {
                vm.updatingAddress = false;
                vm.call_email.email_user = response;
                if (vm.call_email.email_user.residential_address == null){ vm.call_email.email_user.residential_address = {}; }
                swal.fire({
                    title: 'Update Address Details',
                    html: 'User address details has been successfully updated.',
                    type: 'success',
                })
            }, (error) => {
                vm.updatingAddress = false;
                let error_msg = '<br/>';
                for (var key in error.body) {
                    error_msg += key + ': ' + error.body[key] + '<br/>';
                }
                swal.fire({
                    title: 'Update Address Details',
                    html: 'There was an error updating the user address details.<br/>' + error_msg,
                    type: 'error'
                })
            });
        },
        loadCountries: function(){
            let vm = this;
            let initialisers = [
                utils.fetchCountries(),
            ]
            Promise.all(initialisers).then(data => {
                vm.countries = data[0];
            });
        },
        loadEmailUser: function(id){
            let vm = this;
            let initialisers = [
                utils.fetchUser(id),
            ]
            Promise.all(initialisers).then(data => {
                vm.call_email.email_user = data[0];
                if(vm.call_email.email_user.residential_address == null){
                    vm.call_email.email_user.residential_address = {
                        line1: '',
                        locality: '',
                        state: 'WA',
                        postcode: '',
                        country: 'AU'
                    }
                }
                vm.call_email.email_user.residential_address = vm.call_email.email_user.residential_address != null ? vm.call_email.email_user.residential_address : {};
            });
        },
    }
}
</script>

<style scoped>
.nav-tabs {
    border-bottom: none !important;
}
</style>
