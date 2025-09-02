<template id="returns_dashboard">
    <div class="row">
        <div class="col-sm-12">
            <FormSection
                :form-collapse="false"
                label="Sanction Outcomes"
                index="sanction_outcomes"
                :subtitle=subtitle
            >
                <div class="panel panel-default">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Type</label>
                                <select class="form-control" v-model="filterType">
                                    <option v-for="option in sanction_outcome_types" :value="option.id" v-bind:key="option.id">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Status</label>
                                <select class="form-control" v-model="filterStatus">
                                    <option v-for="option in sanction_outcome_statuses" :value="option.id" v-bind:key="option.id">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Payment status</label>
                                <select class="form-control" v-model="filterPaymentStatus">
                                    <option v-for="option in sanction_outcome_payment_statuses" :value="option.id" v-bind:key="option.id">
                                        {{ option.display }}
                                    </option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-3">
                            <label for="">Issue date from</label>
                            <div class="input-group date" ref="issueDateFromPicker">
                                <input type="date" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateFrom">
                                <!--<span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>-->
                            </div>
                        </div>
                        <div class="col-md-3">
                            <label for="">Issue date to</label>
                            <div class="input-group date" ref="issueDateToPicker">
                                <input type="date" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateTo">
                                <!--<span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>-->
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-lg-12">
                            <datatable ref="sanction_outcome_table" id="datatable_id" :dtOptions="table_options" :dtHeaders="table_headers"/>
                        </div>
                    </div>
                </div>
            </FormSection>
        </div>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import datatable from '@vue-utils/datatable.vue'
import { api_endpoints, helpers, cache_helper, fetch_util } from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'SanctionOutcomeTableDash',
    props: {
        level:{
            type: String,
            required: true,
            validator:function(val) {
                let options = ['internal','external'];
                return options.indexOf(val) != -1 ? true: false;
            }
        },
        url:{
            type: String,
            required: true
        }
    },
    data() {
        let vm = this;
        return {
            sanction_outcome_types: [],
            sanction_outcome_statuses: [],
            sanction_outcome_payment_statuses: [],

            pBody: 'pBody' + uuid(),
            datatable_id: 'return-datatable-'+uuid(),

            filterType: 'all',
            filterStatus: 'all',
            filterPaymentStatus: 'all',
            filterDateFrom: '',
            filterDateTo: '',

            dateFormat: 'YYYY-MM-DD',
            datepickerOptions:{
                format: 'YYYY-MM-DD',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            table_headers:["id", "Number", "Type", "Identifier", "Date", "Status", "Payment Status", "Sanction Outcome", "Action", ""],
            table_options:{
                serverSide: true,
                searchDelay: 1000,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                processing: true,
                ajax: {
                    url: vm.url,
                    dataSrc: 'data',
                    data: function (d) {
                        d.type = vm.filterType;
                        d.status = vm.filterStatus;
                        d.payment_status = vm.filterPaymentStatus;
                        d.date_from = vm.filterDateFrom;
                        d.date_to = vm.filterDateTo;
                    },
                    complete: function(jqXHR, textStatus){
                        // A function to be called when the request succeeds.
                        vm.$emit('records_total', jqXHR.responseJSON.recordsTotal);
                    }
                },
                columns: [
                    {
                        data: 'id',
                        visible: false,
                    },
                    {
                        data: 'lodgement_number',
                        searchable: true,
                        orderable: true,
                    },
                    {
                        data: 'type',
                        searchable: true,
                        orderable: true,
                        mRender: function (data, type, full) {
                            return data.name;
                        }
                    },
                    {
                        data: 'identifier',
                        searchable: true,
                        orderable: true,
                    },
                    {
                        data: 'date_of_issue',
                        searchable: true,
                        orderable: true,
                        mRender: function (data, type, full) {
                            return data != '' && data != null ? moment(data).format('YYYY-MM-DD') : '';
                        }
                    },
                    {
                        data: 'status',
                        searchable: true,
                        orderable: true,
                        mRender: function (data, type, full) {
                            return data.name;
                        }
                    },
                    {
                        data: 'payment_status.name',
                        searchable: true,
                        orderable: true,
                    },
                    {
                        data: 'paper_notices',
                        searchable: true,
                        orderable: false,
                        mRender: function (data, type, row){
                            console.log(row)
                            return data;
                        }
                    },
                    {
                        data: 'user_action',
                        mRender: function (data, type, full) {
                            return data;
                        }
                    },
                    // Remediation Actions
                    {
                        data: 'remediation_actions',
                        mRender: function (data, type, full) {
                            let html = ''

                            if (full.remediation_actions && full.remediation_actions.length){
                                let body = ''
                                let td = '<td col="row">'
                                let td_close = '</td>'
                                let th = '<th scope="col">'
                                let th_close = '</th>'

                                for (let i=0; i<full.remediation_actions.length; i++){
                                    let ra = full.remediation_actions[i];
                                    body += '<tr>' +
                                        //td + ra.description + td_close +
                                        td + moment(ra.due_date).format('YYYY-MM-DD') + td_close +
                                        td + ra.status.name + td_close +
                                        td + ra.user_action + td_close
                                    '</tr>'
                                }

                                let header = '<thead><tr>' +
                                    //th + 'Description' + th_close +
                                    th + 'Due Date' + th_close +
                                    th + 'Status' + th_close +
                                    th + 'Action' + th_close +
                                    '</tr></thead>'
                                html = '<table class="table">' + header + body + '</table>'
                            }

                            return html
                        }
                    }
                ],
            }
        }
    },
    components:{
        datatable,
        FormSection
    },
    watch:{
        filterType: function () {
            console.log('filterType');
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
        filterStatus: function () {
            console.log('filterStatus');
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
        filterPaymentStatus: function () {
            console.log('filterPaymentStatus');
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
        filterDateFrom: function () {
            console.log('filterDateFrom')
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
        filterDateTo: function () {
            console.log('filterDateTo')
            this.$refs.sanction_outcome_table.vmDataTable.draw();
        },
    },
    computed: {
        is_external: function(){
            return this.level == 'external';
        },
        subtitle: function() {
            if (this.is_external) {
                return "View any sanction outcome issued to you, pay any infringement notice and follow up on any remediation action";
            }
            return "";
        }
    },
    created: async function(){
        this.constructOptionsType();
        this.constructOptionsStatus();
        this.constructOptionsPaymentStatus();
    },
    methods:{
        addEventListeners: function () {
            let vm = this;
            // External Pay Fee listener
            vm.$refs.sanction_outcome_table.vmDataTable.on('click', 'a[data-pay-infringement-penalty]', function(e) {
                e.preventDefault();
                var id = $(e.target).attr('data-pay-infringement-penalty');
                vm.payInfringementPenalty(id);
            });
        },
        payInfringementPenalty: function(sanction_outcome_id){
            let request = fetch_util.fetchUrl('/infringement_penalty/' + sanction_outcome_id + '/',{method:'POST'})
            request.then(res=>{
                    window.location.href = res;
                },err=>{
                    swal.fire(
                        'Submit Error',
                        helpers.apiVueResourceError(err),
                        'error'
                    )
                });
        },
        constructOptionsType: async function() {
            let returned = await cache_helper.getSetCacheList('SanctionOutcomeTypes', '/api/sanction_outcome/types.json');
            Object.assign(this.sanction_outcome_types, returned);
            this.sanction_outcome_types.splice(0, 0, {id: 'all', display: 'All'});
        },
        constructOptionsStatus: async function() {
            let returned = await cache_helper.getSetCacheList('SanctionOutcomeStatuses', '/api/sanction_outcome/statuses_for_external.json');
            Object.assign(this.sanction_outcome_statuses, returned);
            this.sanction_outcome_statuses.splice(0, 0, {id: 'all', display: 'All'});
        },
        constructOptionsPaymentStatus: async function() {
            let returned = await cache_helper.getSetCacheList('SanctionOutcomePaymentStatuses', '/api/sanction_outcome/payment_statuses.json');
            Object.assign(this.sanction_outcome_payment_statuses, returned);
            this.sanction_outcome_payment_statuses.splice(0, 0, {id: 'all', display: 'All'});
        },
    },
    mounted: function(){
        let vm = this;
        this.$nextTick(() => {
            vm.addEventListeners();
            //vm.initialiseSearch();
        });
    }
}
</script>