<template>
<div class="container" id="internalOrgAccess">
    <div class="row">
        <h3>Organisation Access Request {{ access.id }}</h3>
        <div class="col-md-4">
            <CommsLogs :comms_url="comms_url" :logs_url="logs_url" comms_add_url="test"/>
            <div class="">
                <div class="card mb-3">
                    <div class="card-header">
                       Submission 
                    </div>
                    <div class="card-body border-bottom">
                        <div class="row">
                            <div class="col-sm-12">
                                <strong>Submitted by</strong><br/>
                                {{ access.requester.full_name }}
                            </div>
                            <div class="col-sm-12 top-buffer-s">
                                <strong>Lodged on</strong><br/>
                                {{ formatDate(access.lodgement_date) }}
                            </div>
                            <div class="col-sm-12 top-buffer-s">
                                <table class="table small-table">
                                    <thead>
                                    <tr>
                                        <th>Lodgment</th>
                                        <th>Date</th>
                                        <th>Action</th>
                                    </tr>
                                    </thead>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="card mb-3">
                    <div class="card-header">
                        Workflow 
                    </div>
                    <div class="card-body border-bottom">
                        <div class="row">
                            <div class="col-sm-12">
                                <strong>Status</strong><br/>
                                {{ access.status.name }}
                            </div>
                             <div class="col-sm-12 top-buffer-s">
                                <strong>Assigned Officer</strong><br/>
                                <div class="form-group">
                                    <div>
                                        <select ref="assigned_officer" :disabled="!officerCanProcess" class="form-control" v-model="access.assigned_officer">
                                            <option v-for="member in organisation_access_group_members" :value="member.id" v-bind:key="member.id">{{member.name}}</option>
                                        </select>
                                        <a v-if="officerCanProcess" @click.prevent="assignToMe()" class="actionBtn pull-right">Assign to me</a>
                                    </div>
                                </div>
                            </div>
                            <div class="col-sm-12 top-buffer-s" v-if="officerCanProcess">
                                <strong>Action</strong><br/>
                                <button v-if="!isAmendmentRequested" class="btn btn-primary" @click.prevent="acceptRequest()">Accept</button>
                                <button v-if="isAmendmentRequested" disabled class="btn btn-primary">Accept</button><br/>
                                <button v-if="!isAmendmentRequested" class="btn btn-primary top-buffer-s" @click.prevent="amendmentRequest()">Request Amendment</button>
                                <button v-if="isAmendmentRequested" disabled class="btn btn-primary top-buffer-s">Amendment Requested</button><br/>
                                <button class="btn btn-primary top-buffer-s" @click.prevent="declineRequest()">Decline</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="col-md-8">
            <div class="row">
                <div class="panel panel-default">
                    <div class="panel-heading">
                        <h3>Organisation Access Request {{ requestType }}</h3>
                    </div>
                    <div class="panel-body panel-collapse">
                        <div class="row">
                            <div class="col-sm-12">
                                <form class="form-horizontal" name="access_form">
                                    <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Organisation</label>
                                        <div class="col-sm-6">
                                            <input type="text" disabled class="form-control" name="name" placeholder="" v-model="access.name">
                                        </div>
                                    </div>   
                                    <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">ABN</label>
                                        <div class="col-sm-6">
                                            <input type="text" disabled class="form-control" name="abn" placeholder="" v-model="access.abn">
                                        </div>
                                    </div>   
                                    <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Letter</label>
                                        <div class="col-sm-6">
                                            <a target="_blank" :href="access.identification"><i class="fa fa-file-pdf-o"></i>&nbsp;Organisation Proof Document</a>
                                        </div>
                                    </div>   
                                    <div class="form-group" style="margin-top:50px;">
                                        <label for="" class="col-sm-3 control-label">Phone</label>
                                        <div class="col-sm-6">
                                            <input type="text" disabled class="form-control" name="phone" placeholder="" v-model="access.requester.phone_number">
                                        </div>
                                    </div>   
                                    <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Mobile</label>
                                        <div class="col-sm-6">
                                            <input type="text" disabled class="form-control" name="mobile" placeholder="" v-model="access.requester.mobile_number">
                                        </div>
                                    </div>   
                                    <div class="form-group">
                                        <label for="" class="col-sm-3 control-label">Email</label>
                                        <div class="col-sm-6">
                                            <input type="text" disabled class="form-control" name="email" placeholder="" v-model="access.requester.email">
                                        </div>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
</template>
<script>
import Vue from 'vue'
import datatable from '@vue-utils/datatable.vue'
import CommsLogs from '@common-components/comms_logs.vue'
import {
  api_endpoints,
  helpers, fetch_util
}
from '@/utils/hooks'
export default {
  name: 'OrganisationAccess',
  data() {
    let vm = this;
    return {
        loading: [],
        access: {
            requester: {},
            status: {},
        },
        initialisedSelects: false,
        DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
        organisation_access_group_members: [],
        // Filters
        logs_url: helpers.add_endpoint_json(api_endpoints.organisation_requests,vm.$route.params.access_id+'/action_log'),
        comms_url: helpers.add_endpoint_json(api_endpoints.organisation_requests,vm.$route.params.access_id+'/comms_log'),
        actionDtOptions:{
            language: {
                processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
            },
            responsive: true,
            deferRender: true, 
            autowidth: true,
            order: [[2, 'desc']],
            dom:
                "<'row'<'col-sm-5'l><'col-sm-6'f>>" +
                "<'row'<'col-sm-12'tr>>" +
                "<'row'<'col-sm-5'i><'col-sm-7'p>>",
            processing:true,
            ajax: {
                "url": helpers.add_endpoint_json(api_endpoints.organisation_requests,vm.$route.params.access_id+'/action_log'),
                "dataSrc": '',
            },
            columns:[
                {
                    data:"who",
                },
                {
                    data:"what",
                },
                {
                    data:"when",
                    mRender:function(data,type,full){
                        return moment(data).format(vm.DATE_TIME_FORMAT)
                    }
                },
            ]
        },
        dtHeaders:["Who","What","When"],
        actionsTable : null,
        commsDtOptions:{
            language: {
                processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
            },
            responsive: true,
            deferRender: true, 
            autowidth: true,
            order: [[0, 'desc']],
            processing:true,
            ajax: {
                "url": helpers.add_endpoint_json(api_endpoints.organisation_requests,vm.$route.params.access_id+'/comms_log'),
                "dataSrc": '',
            },
            columns:[
                {
                    title: 'Date',
                    data: 'created',
                    render: function (date) {
                        return moment(date).format(vm.DATE_TIME_FORMAT);
                    }
                },
                {
                    title: 'Type',
                    data: 'type'
                },
                {
                    title: 'Reference',
                    data: 'reference'
                },
                {
                    title: 'To',
                    data: 'to',
                    render: vm.commaToNewline
                },
                {
                    title: 'CC',
                    data: 'cc',
                    render: vm.commaToNewline
                },
                {
                    title: 'From',
                    data: 'fromm',
                    render: vm.commaToNewline
                },
                {
                    title: 'Subject/Desc.',
                    data: 'subject'
                },
                {
                    title: 'Text',
                    data: 'text',
                    'render': function (value) {
                        var ellipsis = '...',
                            truncated = _.truncate(value, {
                                length: 100,
                                omission: ellipsis,
                                separator: ' '
                            }),
                            result = '<span>' + truncated + '</span>',
                            popTemplate = _.template('<a href="#" ' +
                                'role="button" ' +
                                'data-toggle="popover" ' +
                                'data-trigger="click" ' +
                                'data-placement="top auto"' +
                                'data-html="true" ' +
                                'data-content="<%= text %>" ' +
                                '>more</a>');
                        if (_.endsWith(truncated, ellipsis)) {
                            result += popTemplate({
                                text: value
                            });
                        }

                        return result;
                    },
                },
                {
                    title: 'Documents',
                    data: 'documents',
                    'render': function (values) {
                        var result = '';
                        _.forEach(values, function (value) {
                            // We expect an array [docName, url]
                            // if it's a string it is the url
                            var docName = '',
                                url = '';
                            if (_.isArray(value) && value.length > 1){
                                docName = value[0];
                                url = value[1];
                            }
                            if (typeof s === 'string'){
                                url = value;
                                // display the first  chars of the filename
                                docName = _.last(value.split('/'));
                                docName = _.truncate(docName, {
                                    length: 18,
                                    omission: '...',
                                    separator: ' '
                                });
                            }
                            result += '<a href="' + url + '" target="_blank"><p>' + docName+ '</p></a><br>';
                        });
                        return result;
                    }
                }
            ]
        },
        commsTable : null,
        requestType : null,
    }
  },
  beforeRouteEnter: function(to, from, next){
    let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,to.params.access_id))
    request.then((response) => {
        next(vm => {
            vm.access = response
            vm.requestType = vm.access.role == 'employee' ? '(Administrator)' : '(Consultant)'
        })
    }).catch((error) => {
        console.log(error);
    });
  },
  components: {
    datatable,
    CommsLogs
  },
  computed: {
    isLoading: function () {
      return this.loading.length > 0;
    },
    isFinalised: function(){
        return this.access.status.id == 'approved' || this.access.status.id == 'declined';
    },
    isAmendmentRequested: function(){
        return this.access.status.id == 'amendment_requested';
    },
    officerCanProcess: function(){
        return this.access && this.access.can_be_processed && !this.isFinalised && this.access.user_can_process_org_access_requests ? true : false;
    }
  },
  methods: {
    commaToNewline(s){
        return s.replace(/[,;]/g, '\n');
    },
    fetch_utilAccessGroupMembers: function(){
        let vm = this;
        vm.loading.push('Loading Access Group Members');
        let request = fetch_util.fetchUrl(api_endpoints.organisation_access_group_members).then((response) => {
            vm.organisation_access_group_members = response
            vm.loading.splice('Loading Access Group Members',1);
        }).catch((error) => {
            console.log(error);
            vm.loading.splice('Loading Access Group Members',1);
        })

    },
    assignToMe: function(){
        let vm = this;
        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,(vm.access.id+'/assign_to_me')))
        request.then((response) => {
            vm.access = response;
            vm.updateAssignedOfficerSelect();
        }).catch((error) => {
            vm.updateAssignedOfficerSelect();
            swal.fire(
                'Application Error',
                helpers.apiVueResourceError(error),
                'error'
            )
        });
    },
    assignOfficer: function(){
        let vm = this;
        let unassign = true;
        let data = {};
        unassign = vm.access.assigned_officer != null && vm.access.assigned_officer != 'undefined' ? false: true;
        data = {'officer_id': vm.access.assigned_officer};
        if (!unassign){
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,(vm.access.id+'/assign_officer')), {method:'POST', body:JSON.stringify(data)},{
                emulateJSON:true
            })
            request.then((response) => {
                vm.access = response;
                vm.updateAssignedOfficerSelect();
            }).catch((error) => {
                vm.updateAssignedOfficerSelect();
                swal.fire(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        }
        else{
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,(vm.access.id+'/unassign_officer')))
            request.then((response) => {
                vm.access = response;
                vm.updateAssignedOfficerSelect();
            }).catch((error) => {
                vm.updateAssignedOfficerSelect();
                swal.fire(
                    'Application Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        }
    },
    updateAssignedOfficerSelect:function(){
        let vm = this;
        $(vm.$refs.assigned_officer).val(vm.access.assigned_officer);
        $(vm.$refs.assigned_officer).trigger('change');
    },
    acceptRequest: function() {
        let vm = this;
        swal.fire({
            title: "Accept Organisation Request",
            text: "Are you sure you want to accept this organisation request?",
            type: "question",
            showCancelButton: true,
            confirmButtonText: 'Accept'
        }).then((result) => {
            if (result) {
                let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,(vm.access.id+'/accept')))
                request.then((response) => {
                    swal.fire({
                        title: "Accept Organisation Request",
                        text: "The organisation access request has been accepted.",
                        type: "success"}
                    );
                    vm.access = response;
                }).catch((error) => {
                    swal.fire({
                        title: "Accept Organisation Request",
                        text: "There was an error accepting the organisation access request.",
                        type: "error"}
                    );
                    console.log(error);
                });
            }
        }).catch((error) => {
            console.log(error)
        });

    },
    amendmentRequest: function() {
        let vm = this;
        swal.fire({
            title: "Amendment Request",
            text: "Request a new letter from the user.",
            type: "question",
            input: "textarea",
            inputPlaceholder: 'Type your reason for your amendment request here',
            showCancelButton: true,
            confirmButtonText: 'Send Request'
        }).then((result) => {
            if (result) {
                let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,(vm.access.id+'/amendment_request/?reason='+result)))
                request.then((response) => {
                    swal.fire({
                        title: "Amendment Request",
                        text: "A new letter has been requested.",
                        type: "success"}
                    );
                    vm.access = response;
                }).catch((error) => {
                    swal.fire({
                        title: "Amendment Request",
                        text: "There was an error sending the amendment request request.",
                        type: "error"}
                    );
                    console.log(error);
                });
            }
        }).catch((error) => {
            console.log(error)
        });

    },
    declineRequest: function() {
        let vm = this;
        swal.fire({
            title: "Decline Organisation Request",
            text: "Are you sure you want to decline this organisation request?",
            type: "question",
            showCancelButton: true,
            confirmButtonText: 'Accept'
        }).then((result) => {
            if (result) {
                let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,(vm.access.id+'/decline')))
                request.then((response) => {
                    swal.fire({
                        title: "Decline Organisation Request",
                        text: "The organisation access request has been declined.",
                        type: "success"}
                    );
                    vm.access = response;
                }).catch((error) => {
                    swal.fire({
                        title: "Decline Organisation Request",
                        text: "There was an error declining the organisation access request.",
                        type: "error"}
                    );
                });
            }
        },(error) => {

        });

    },
    initialiseAssignedOfficerSelect:function(reinit=false){
        let vm = this;
        if (reinit){
            $(vm.$refs.assigned_officer).data('select2') ? $(vm.$refs.assigned_officer).select2('destroy'): '';
        }
        // Assigned officer select
        $(vm.$refs.assigned_officer).select2({
            "theme": "bootstrap",
            allowClear: true,
            placeholder:"Select Officer"
        }).
        on("select2:select",function (e) {
            var selected = $(e.currentTarget);
            vm.access.assigned_officer = selected.val();
            vm.assignOfficer();
        }).on("select2:unselecting", function(e) {
            var self = $(this);
            setTimeout(() => {
                self.select2('close');
            }, 0);
        }).on("select2:unselect",function (e) {
            var selected = $(e.currentTarget);
            vm.access.assigned_officer = null;
            vm.assignOfficer();
        });
    },
    initialiseSelects: function(){
        let vm = this;
        if (!vm.initialisedSelects){
            vm.initialiseAssignedOfficerSelect();
            vm.initialisedSelects = true;
        }
    },
  },
  mounted: function () {
    let vm = this;
    this.fetchAccessGroupMembers();
  },
    updated: function(){
        let vm = this;
        this.$nextTick(() => {
            vm.initialiseSelects();
        });
    },
}
</script>
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
</style>
