<template>
    <div class="container" id="userInfo">
        <div class="row">
            <div class="col-sm-12">
                <div class="panel panel-default">
                  <div class="panel-heading">
                    <h3 class="panel-title">Organisations <small>Link to the Organisations you are an employee of and for which you are managing licences</small>
                        <a class="panelClicker" :href="'#'+oBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="oBody">
                            <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                        </a>
                    </h3>
                  </div>
                  <div class="panel-body collapse in" :id="oBody">
                      <form class="form-horizontal" name="orgForm" method="post">
                          <div class="form-group">
                            <label for="" class="col-sm-5 control-label">Do you manage licences on behalf of an organisation?</label>
                            <div class="col-sm-4">
                                 <label class="radio-inline">
                                  <input :disabled="hasOrgs" type="radio" name="behalf_of_org" v-model="managesOrg" value="No" > No
                                </label>
                                <label class="radio-inline">
                                  <input type="radio" name="behalf_of_org" v-model="managesOrg" value="Yes"> Yes
                                </label>
                                 <label class="radio-inline">
                                  <input type="radio" name="behalf_of_org" v-model="managesOrg" value="Consultant"> Yes, as a consultant
                                </label>
                            </div>
                            <div v-if="managesOrg=='Yes'">
                                <div class="col-sm-3">
                                    <button class="btn btn-primary" v-if="hasOrgs && !addingCompany" @click.prevent="addCompany()">Add Another Organisation</button>
                                </div>
                            </div>
                          </div>
                          <div v-for="org in current_user.wildlifecompliance_organisations" v-bind:key="org.id">
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >Organisation</label>
                                <div class="col-sm-3"> 
                                    <input type="text" disabled class="form-control" name="organisation" v-model="org.name" placeholder="">
                                </div>
                                <label for="" class="col-sm-1 control-label" >ABN/ACN</label>
                                <div class="col-sm-3"> 
                                    <input type="text" disabled class="form-control" name="organisation" v-model="org.abn" placeholder="">
                                </div>
                                <a style="cursor:pointer;text-decoration:none;" @click.prevent="unlinkUser(org)"><i class="fa fa-chain-broken fa-2x" ></i>&nbsp;Unlink</a>
                              </div>
                          </div>
                          <div v-for="orgReq in orgRequest_pending" v-bind:key="orgReq.id">
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >Organisation</label>
                                <div class="col-sm-3"> 
                                    <input type="text" disabled class="form-control" name="organisation" v-model="orgReq.name" placeholder="">
                                </div>
                                <label for="" class="col-sm-1 control-label" >ABN/ACN</label>
                                <div class="col-sm-3"> 
                                    <input type="text" disabled class="form-control" name="organisation" v-model="orgReq.abn" placeholder="">
                                </div>
                                <label><i class="fa fa-hourglass-o fa-2x" ></i> Pending Approval</label>
                              </div>
                          </div>
                          <div v-for="orgReq in orgRequest_amendment_requested" v-bind:key="orgReq.id">
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >Organisation</label>
                                <div class="col-sm-3">
                                    <input type="text" disabled class="form-control" name="organisation" v-model="orgReq.name" placeholder="">
                                </div>
                                <label for="" class="col-sm-1 control-label" >ABN/ACN</label>
                                <div class="col-sm-3">
                                    <input type="text" disabled class="form-control" name="organisation" v-model="orgReq.abn" placeholder="">
                                </div>
                                    <span class="btn btn-info btn-file pull-left">
                                        Upload New File <input type="file" ref="uploadedFile" @change="uploadNewFileUpdateOrgRequest(orgReq)"/>
                                    </span>
                                    <span class="pull-left" style="margin-left:10px;margin-top:10px;">{{uploadedFileName}}</span>
                              </div>
                          </div>

                          <div v-if="managesOrg=='Consultant' && addingCompany">
                              <h3>New Organisation (as consultant)</h3>
                              <div class="form-group">
                                  <label for="" class="col-sm-2 control-label" >Organisation</label>
                                  <div class="col-sm-6">
                                      <input type="text" class="form-control" name="organisation" v-model="newOrg.name" placeholder="">
                                  </div>
                              </div>
                              <div class="form-group">
                                  <label for="" class="col-sm-2 control-label" >ABN/ACN</label>
                                  <div class="col-sm-6">
                                      <input type="text" class="form-control" name="abn" v-model="newOrg.abn" placeholder="">
                                  </div>
                                  <div class="col-sm-2">
                                      <button v-if="newOrg.detailsChecked" @click.prevent="checkOrganisation()" class="btn btn-primary">Check Details</button>
                                  </div>
                              </div>
                              <div class="form-group">
                                    <label class="col-sm-12" style="text-align:left;">
                                      Please upload a letter with an organisation letterhead stating that you are a consultant for the organisation.
                                        <span class="btn btn-info btn-file">
                                            Atttach File <input type="file" ref="uploadedFile" @change="readFile()"/>
                                        </span>
                                        <span  style="margin-left:10px;margin-top:10px;">{{uploadedFileName}}</span>
                                    </label>
                                    <br/>

                                    <label for="" class="col-sm-10 control-label" style="text-align:left;">You will be notified by email once the Department has checked the organisation details.
                                    </label>


                                    <div class="col-sm-12">
                                      <button v-if="!registeringOrg" @click.prevent="orgConsultRequest()" class="btn btn-primary pull-left">Submit</button>
                                      <button v-else disabled class="btn btn-primary pull-right"><i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting</button>
                                    </div>
                              </div>
                           </div>




                          <div style="margin-top:15px;" v-if="managesOrg=='Yes' && addingCompany">
                              <h3>New Organisation</h3>
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >Organisation</label>
                                <div class="col-sm-6">
                                    <input type="text" class="form-control" name="organisation" v-model="newOrg.name" placeholder="">
                                </div>
                              </div>
                              <div class="form-group">
                                <label for="" class="col-sm-2 control-label" >ABN/ACN</label>
                                <div class="col-sm-6">
                                    <input type="text" class="form-control" name="abn" v-model="newOrg.abn" placeholder="">
                                </div>
                                <div class="col-sm-2">
                                    <button @click.prevent="checkOrganisation()" class="btn btn-primary">Check Details</button>
                                </div>
                              </div>
                              <div class="form-group" v-if="newOrg.exists && newOrg.detailsChecked">
                                  <label class="col-sm-12" style="text-align:left;margin-bottom:20px;">
                                    This organisation has already been registered with the system. Please enter the two pin codes below.<br/>
                                    These pin codes can be retrieved from one of the following people:<br/> {{newOrg.first_five}}
                                  </label>
                                  <label for="" class="col-sm-2 control-label" >Pin 1</label>
                                  <div class="col-sm-2">
                                    <input type="text" class="form-control" name="abn" v-model="newOrg.pin1" placeholder="">
                                  </div>
                                  <label for="" class="col-sm-2 control-label" >Pin 2</label>
                                  <div class="col-sm-2">
                                    <input type="text" class="form-control" name="abn" v-model="newOrg.pin2" placeholder="">
                                  </div>
                                  <div class="col-sm-2">
                                    <button v-if="!validatingPins" @click.prevent="validatePins()" class="btn btn-primary pull-left">Validate</button>
                                    <button v-else class="btn btn-primary pull-left"><i class="fa fa-spin fa-spinner"></i>&nbsp;Validating Pins</button>
                                  </div>
                              </div>
                              <div class="form-group" v-else-if="!newOrg.exists && newOrg.detailsChecked">
                                  <label class="col-sm-12" style="text-align:left;">
                                    This organisation has not yet been registered with this system. Please upload a letter with an organisation letterhead stating that you are an employee of this organisation.<br/>
                                  </label>
                                  <div class="col-sm-12">
                                    <span class="btn btn-info btn-file pull-left">
                                        Attach File <input type="file" ref="uploadedFile" @change="readFile()"/>
                                    </span>
                                    <span class="pull-left" style="margin-left:10px;margin-top:10px;">{{uploadedFileName}}</span>
                                  </div>
                                  <label for="" class="col-sm-10 control-label" style="text-align:left;">You will be notified by email once the Department has checked the organisation details.</label>
                                  <div class="col-sm-12">
                                    <button v-if="!registeringOrg" @click.prevent="orgRequest()" class="btn btn-primary pull-right">Submit</button>
                                    <button v-else disabled class="btn btn-primary pull-right"><i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting</button>
                                  </div>
                              </div>
                              <div class="form-group" v-else-if="newOrg.exists && !newOrg.detailsChecked">
                                  <label class="col-sm-12" style="text-align:left;">
                                    Please upload a letter with an organisation letterhead stating that you are an employee of this organisation.<br/>
                                  </label>
                                  <div class="col-sm-12">
                                    <span class="btn btn-info btn-file pull-left">
                                        Attach File <input type="file" ref="uploadedFile" @change="readFile()"/>
                                    </span>
                                    <span class="pull-left" style="margin-left:10px;margin-top:10px;">{{uploadedFileName}}</span>
                                  </div>
                                  <label for="" class="col-sm-10 control-label" style="text-align:left;">You will be notified by email once the Department has checked the organisation details.</label>
                                  <div class="col-sm-12">
                                    <button v-if="!registeringOrg" @click.prevent="orgRequest()" class="btn btn-primary pull-right">Submit</button>
                                    <button v-else disabled class="btn btn-primary pull-right"><i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting</button>
                                  </div>
                              </div>
                              
                        </div>
                       </form>
                  </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import Vue from 'vue'
import $ from 'jquery'
import { api_endpoints, helpers } from '@/utils/hooks'
import SecureBaseLink from '@/components/common/securebase_link.vue';
export default {
    name: 'MyUserDetails',
    components: {
        SecureBaseLink,
    },
    data () {
        let vm = this;
        return {
            oBody: 'oBody'+vm._uid,
            current_user: {
                wildlifecompliance_organisations:[],
            },
            newOrg: {
                'name': '',
                'abn': '',
                'detailsChecked': false,
                'exists': false
            },
            loading: [],
            registeringOrg: false,
            validatingPins: false,
            addingCompany: false,
            managesOrg: 'No',
            managesOrgConsultant: 'No',
            uploadedFile: null,
            uploadedID: null,

            updatingPersonal: false,
            updatingAddress: false,
            updatingContact: false,
            role:null,
            orgRequest_pending:[],
            orgRequest_amendment_requested:[],
            new_user: false,
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            showCompleteMsg:false,
        }
    },
    watch: {
        managesOrg: function() {
            if (this.managesOrg == 'Yes'){
              this.newOrg.detailsChecked = false;
              this.role = 'employee'
            } else if (this.managesOrg == 'Consultant'){
              this.newOrg.detailsChecked = false;
              this.role ='consultant'
            }else{this.role = null
              this.newOrg.detailsChecked = false;
            }

            if (this.managesOrg  == 'Yes' && !this.hasOrgs && this.newOrg){
                this.addCompany()

            } else if (this.managesOrg == 'No' && this.newOrg){
                this.resetNewOrg();
                this.uploadedFile = null;
                this.addingCompany = false;
            } else if (this.managesOrg == 'Consultant' && this.newOrg) {
                this.addCompany();
            } else {
                this.addCompany()
                this.addingCompany=false
            }
        },
  
    },
    computed: {
        hasOrgs: function() {
            if (this.current_user) {
                return this.current_user.wildlifecompliance_organisations && this.current_user.wildlifecompliance_organisations.length > 0 ? true: false;
            }
            return false;
        },
        uploadedFileName: function() {
            return this.uploadedFile != null ? this.uploadedFile.name: '';
        },
    },
    methods: {
        readFile: function() {
            let vm = this;
            let _file = null;
            var input = $(vm.$refs.uploadedFile)[0];
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(input.files[0]); 
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            vm.uploadedFile = _file;
        },
        readFileID: async function() {
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
            await vm.uploadID();
        },
        addCompany: function (){
            this.newOrg.push = {
                'name': '',
                'abn': '',
            };
            this.addingCompany=true;
        },
        resetNewOrg: function(){
            this.newOrg = {
                'detailsChecked': false,
                'exists': false
            };
        },
        checkOrganisation: function() {
            console.log('Entered CheckOrg')
            let vm = this;
            let new_organisation = vm.newOrg;
            for (var organisation in vm.current_user.wildlifecompliance_organisations) {
                if (new_organisation.abn && vm.current_user.wildlifecompliance_organisations[organisation].abn == new_organisation.abn) {
                    swal({
                        title: 'Checking Organisation',
                        html: 'You are already associated with this organisation.',
                        type: 'info'
                    })
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();
                    return;
                }
            }
            vm.$http.post(helpers.add_endpoint_json(api_endpoints.organisations,'existence'),JSON.stringify(this.newOrg),{
                emulateJSON:true
            }).then((response) => {
                this.newOrg.exists = response.body.exists;
                this.newOrg.id = response.body.id;
                this.newOrg.detailsChecked = false;
                if (response.body.first_five) {
                  this.newOrg.first_five = response.body.first_five;
                  this.newOrg.detailsChecked = true;
                }
                this.newOrg.detailsChecked = this.newOrg.exists ? this.newOrg.detailsChecked : true;
            }, (error) => {
                this.newOrg.detailsChecked = false;
                let error_msg = '<br/>';
                for (var key in error.body) {
                    if (key==='non_field_errors'){
                        error_msg += error.body[key] + '<br/>';
                    } else {
                        error_msg += key + ': ' + error.body[key] + '<br/>';
                    }
                }
                swal({
                    title: 'Checking Organisation',
                    html: 'There was an error checking this organisation.<br/>' + error_msg,
                    type: 'error'
                })
            });
        },
        validatePins: function() {
            let vm = this;
            vm.validatingPins = true;
            vm.$http.post(helpers.add_endpoint_json(api_endpoints.organisations,(vm.newOrg.id+'/validate_pins')),JSON.stringify(this.newOrg),{
                emulateJSON:true
            }).then((response) => {
                if (response.body.valid){
                    swal(
                        'Validate Pins',
                        'The pins you entered have been validated and your request will be processed by Organisation Administrator.',
                        'success'
                    )
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();
                    Vue.http.get(api_endpoints.my_user_details).then((response) => {
                        vm.current_user = response.body
                        if ( vm.current_user.wildlifecompliance_organisations && vm.current_user.wildlifecompliance_organisations.length > 0 ) { vm.managesOrg = 'Yes' }
                    },(error) => {
                    })
                }else {
                    swal(
                        'Validate Pins',
                        'The pins you entered were incorrect', 
                        'error'
                    )
                }
                vm.validatingPins = false;
            }, (error) => {
                vm.validatingPins = false;
            });
        },
        orgRequest: function() {
            let vm = this;
            vm.registeringOrg = true;
            let data = new FormData();
            data.append('name', vm.newOrg.name);
            data.append('abn', vm.newOrg.abn);
            data.append('identification', vm.uploadedFile);
            data.append('role',vm.role);
            vm.newOrg.name = vm.newOrg.name == null ? '' : vm.newOrg.name
            vm.newOrg.abn = vm.newOrg.abn == null ? '' : vm.newOrg.abn
            if (vm.newOrg.name == '' || vm.newOrg.abn == '' || vm.uploadedFile == null){
                vm.registeringOrg = false;
                swal(
                    'Error submitting organisation request',
                    'Please enter the organisation details and attach a file before submitting your request.',
                    'error'
                )
            } else {
                vm.$http.post(api_endpoints.organisation_requests,data,{
                    emulateJSON:true
                }).then((response) => {
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();
                    swal({
                        title: 'Sent',
                        html: 'Your organisation request has been successfully submitted.',
                        type: 'success',
                    }).then(() => {
                        if (this.$route.name == 'account'){
                           window.location.reload(true);
                        }
                    });
                }, (error) => {
                    vm.registeringOrg = false;
                    let error_msg = '<br/>';
                    for (var key in error.body) {
                        if (key==='non_field_errors'){
                            error_msg += error.body[key] + '<br/>';
                        } else {
                            error_msg += key + ': ' + error.body[key] + '<br/>';
                        }
                    }
                    swal(
                        'Error submitting organisation request',
                        error_msg,
                        'error'
                    );
                });
            }
        },
        orgConsultRequest: function() {
            let vm = this;
            vm.registeringOrg = true;
            let data = new FormData();
            let new_organisation = vm.newOrg;
            for (var organisation in vm.current_user.wildlifecompliance_organisations) {
                if (new_organisation.abn && vm.current_user.wildlifecompliance_organisations[organisation].abn == new_organisation.abn) {
                    swal({
                        title: 'Checking Organisation',
                        html: 'You are already associated with this organisation.',
                        type: 'info'
                    })
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();
                    return;
                }
            }
            data.append('name', vm.newOrg.name);
            data.append('abn', vm.newOrg.abn);
            data.append('identification', vm.uploadedFile);
            data.append('role',vm.role);
            vm.newOrg.name = vm.newOrg.name == null ? '' : vm.newOrg.name
            vm.newOrg.abn = vm.newOrg.abn == null ? '' : vm.newOrg.abn
            if (vm.newOrg.name == '' || vm.newOrg.abn == '' || vm.uploadedFile == null){
                vm.registeringOrg = false;
                swal(
                    'Error submitting organisation request',
                    'Please enter the organisation details and attach a file before submitting your request.',
                    'error'
                )
            } else {
                vm.$http.post(api_endpoints.organisation_requests,data,{
                    emulateJSON:true
                }).then((response) => {
                    vm.registeringOrg = false;
                    vm.uploadedFile = null;
                    vm.addingCompany = false;
                    vm.resetNewOrg();
                    swal({
                        title: 'Sent',
                        html: 'Your organisation request has been successfully submitted.',
                        type: 'success',
                    }).then(() => {
                        if (this.$route.name == 'account'){
                           window.location.reload(true);
                        }
                    });
                }, (error) => {
                    vm.registeringOrg = false;
                    let error_msg = '<br/>';
                    for (var key in error.body) {
                        if (key==='non_field_errors'){
                            error_msg += error.body[key] + '<br/>';
                        } else {
                            error_msg += key + ': ' + error.body[key] + '<br/>';
                        }
                    }
                    swal(
                        'Error submitting organisation request',
                        error_msg,
                        'error'
                    );
                });
            }
        },
        uploadNewFileUpdateOrgRequest: function(orgReq) {
            let vm = this;
            vm.readFile();
            let data = new FormData();
            data.append('identification', vm.uploadedFile);
            vm.$http.put(helpers.add_endpoint_json(api_endpoints.organisation_requests,orgReq.id+'/reupload_identification_amendment_request'),data,{
                emulateJSON:true
            }).then((response) => {
                vm.uploadedFile = null;
                vm.resetNewOrg();
                swal({
                    title: 'Sent',
                    html: 'Your organisation request has been successfully submitted.',
                    type: 'success',
                }).then(() => {
                    window.location.reload(true);
                });
            }, (error) => {
                console.log(error);
                vm.registeringOrg = false;
                let error_msg = '<br/>';
                for (var key in error.body) {
                    error_msg += key + ': ' + error.body[key] + '<br/>';
                }
                swal(
                    'Error submitting organisation request',
                    error_msg,
                    'error'
                );
            });
        },
        toggleSection: function (e) {
            let el = e.target;
            let chev = null;
            $(el).on('click', function (event) {
                chev = $(this);
                $(chev).toggleClass('glyphicon-chevron-down glyphicon-chevron-up');
            })
        },
        fetchOrgRequestPending:function (){
            let vm =this;
            vm.$http.get(helpers.add_endpoint_json(api_endpoints.organisation_requests,'get_pending_requests')).then((response)=>{
                vm.orgRequest_pending = response.body;
                vm.loading.splice('fetching pending organisation requests',1);
            },(response)=>{
                vm.loading.splice('fetching pending organisation requests',1);
            });
        },
        fetchOrgRequestAmendmentRequested:function (){
            let vm =this;
            vm.$http.get(helpers.add_endpoint_json(api_endpoints.organisation_requests,'get_amendment_requested_requests')).then((response)=>{
                vm.orgRequest_amendment_requested = response.body;
                vm.loading.splice('fetching amendment requested organisation requests',1);
            },(response)=>{
                vm.loading.splice('fetching amendment requested organisation requests',1);
            });
        },
        unlinkUser: function(org){
            let vm = this;
            let org_name = org.name;
            

            swal({
                title: "Unlink From Organisation",
                text: "Are you sure you want to be unlinked from "+org.name+" ?",
                type: "question",
                showCancelButton: true,
                confirmButtonText: 'Accept'
            }).then((result) => {
                if (result) {
                    vm.$http.post(helpers.add_endpoint_json(api_endpoints.organisations,org.id+'/unlink_user'),JSON.stringify(vm.current_user),{
                        emulateJSON:true
                    }).then((response) => {
                        Vue.http.get(api_endpoints.my_user_details).then((response) => {
                            vm.current_user = response.body
                            if ( vm.current_user.wildlifecompliance_organisations && vm.current_user.wildlifecompliance_organisations.length > 0 ) { vm.managesOrg = 'Yes' }
                        },(error) => {
                        })
                        swal(
                            'Unlink',
                            'You have been successfully unlinked from '+org_name+'.',
                            'success'
                        )
                    }, (error) => {
                        let error_msg = '<br/>';
                        for (var key in error.body) {
                            if (key == 'non_field_errors') { error_msg += error.body[key] + '<br/>'; }
                        }
                        swal(
                            'Unlink',
                            'There was an error unlinking you from '+org_name+'.' + error_msg,
                            'error'
                        )
                    });
                }
            },(error) => {
            }); 
        },
    },
    beforeRouteEnter: function(to,from,next){
        Vue.http.get(api_endpoints.my_user_details).then((response) => {
            if (to.name == 'first-time' && response.body.address_details && response.body.personal_details && response.body.contact_details && response.body.has_complete_first_time){
                window.location.href='/';
            }
            else{
                next(vm => {
                    vm.current_user = response.body
                    if (vm.current_user.wildlifecompliance_organisations && vm.current_user.wildlifecompliance_organisations.length > 0) { vm.managesOrg = 'Yes' }
                });
            }
        },(error) => {
        })
    },
    mounted: function(){
        this.fetchOrgRequestPending();
        this.fetchOrgRequestAmendmentRequested();
        this.personal_form = document.forms.personal_form;
        $('.panelClicker[data-toggle="collapse"]').on('click', function () {
            var chev = $(this).children()[0];
            window.setTimeout(function () {
                $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
            },100);
        });
        Vue.http.get(api_endpoints.is_new_user).then((response) => {
            this.new_user = response.body;
        })
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.btn-file {
    position: relative;
    overflow: hidden;
}
.btn-file input[type=file] {
    position: absolute;
    top: 0;
    right: 0;
    min-width: 100%;
    min-height: 100%;
    font-size: 100px;
    text-align: right;
    filter: alpha(opacity=0);
    opacity: 0;
    outline: none;
    background: white;
    cursor: inherit;
    display: block;
}
</style>
