<template id="sanction_outcome_person_org_dashboard">
    <div class="row">
        <div class="col-sm-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Sanction Outcomes
                        <a :href="'#'+pBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                </div>
                <div class="panel-body collapse in" :id="pBody">
                    <div class="row">
                        <div class="col-lg-12">
                            <datatable ref="sanction_outcome_table" id="datatable_id" :dtOptions="table_options" :dtHeaders="table_headers"/>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import datatable from '@/utils/vue/datatable.vue'
import { api_endpoints, helpers, cache_helper } from '@/utils/hooks'

export default {
    name: 'SanctionOutcomePersonOrgTableDash',
    props: {
        level:{
            type: String,
            required: true,
            /*
            validator:function(val) {
                let options = ['internal','external'];
                return options.indexOf(val) != -1 ? true: false;
            }
            */
        },
        entity_id:{
            type: Number,
            required: true
        },
        entity_type:{
            type: String,
            required: true
        },
        /*
        url:{
            type: String,
            required: true
        }
        */
    },
    data() {
        let vm = this;
        return {
            /*
            sanction_outcome_types: [],
            sanction_outcome_statuses: [],
            sanction_outcome_payment_statuses: [],
            */

            pBody: 'pBody' + vm._uid,
            datatable_id: 'return-datatable-'+vm._uid,
            /*
            filterType: 'all',
            filterStatus: 'all',
            filterPaymentStatus: 'all',
            filterDateFrom: '',
            filterDateTo: '',
            */
            dateFormat: 'DD/MM/YYYY',
            datepickerOptions:{
                format: 'DD/MM/YYYY',
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
                    //url: vm.url,
                    url: helpers.add_endpoint_join(api_endpoints.sanction_outcome_paginated,'person_org_datatable_list/?format=datatables'),
                    dataSrc: 'data',
                    data: function (d) {
                        d.entity_id = vm.entity_id;
                        d.entity_type = vm.entity_type;
                        /*
                        d.type = vm.filterType;
                        d.status = vm.filterStatus;
                        d.payment_status = vm.filterPaymentStatus;
                        d.date_from = vm.filterDateFrom;
                        d.date_to = vm.filterDateTo;
                        */
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
                            return data != '' && data != null ? moment(data).format('DD/MM/YYYY') : '';
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
                                        td + moment(ra.due_date).format('DD/MM/YYYY') + td_close +
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
        datatable
    },
    /*
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
    },
    created: async function(){
        this.constructOptionsType();
        this.constructOptionsStatus();
        this.constructOptionsPaymentStatus();
    },
    methods:{
        addEventListeners: function () {
            this.attachFromDatePicker();
            this.attachToDatePicker();

            let vm = this;
            // External Pay Fee listener
            vm.$refs.sanction_outcome_table.vmDataTable.on('click', 'a[data-pay-infringement-penalty]', function(e) {
                e.preventDefault();
                var id = $(e.target).attr('data-pay-infringement-penalty');
                vm.payInfringementPenalty(id);
            });
        },
        payInfringementPenalty: function(sanction_outcome_id){
            this.$http.post('/infringement_penalty/' + sanction_outcome_id + '/').then(res=>{
                    window.location.href = "/ledger/checkout/checkout/payment-details/";
                },err=>{
                    swal(
                        'Submit Error',
                        helpers.apiVueResourceError(err),
                        'error'
                    )
                });
        },
        attachFromDatePicker: function(){
            let vm = this;
            let el_fr = $(vm.$refs.issueDateFromPicker);
            let el_to = $(vm.$refs.issueDateToPicker);

            el_fr.datetimepicker({ format: 'DD/MM/YYYY', maxDate: moment().millisecond(0).second(0).minute(0).hour(0), showClear: true });
            el_fr.on('dp.change', function (e) {
                if (el_fr.data('DateTimePicker').date()) {
                    vm.filterDateFrom = e.date.format('DD/MM/YYYY');
                    el_to.data('DateTimePicker').minDate(e.date);
                } else if (el_fr.data('date') === "") {
                    vm.filterDateFrom = "";
                }
            });
        },
        attachToDatePicker: function(){
            let vm = this;
            let el_fr = $(vm.$refs.issueDateFromPicker);
            let el_to = $(vm.$refs.issueDateToPicker);
            el_to.datetimepicker({ format: 'DD/MM/YYYY', maxDate: moment().millisecond(0).second(0).minute(0).hour(0), showClear: true });
            el_to.on('dp.change', function (e) {
                if (el_to.data('DateTimePicker').date()) {
                    vm.filterDateTo = e.date.format('DD/MM/YYYY');
                    el_fr.data('DateTimePicker').maxDate(e.date);
                } else if (el_to.data('date') === "") {
                    vm.filterDateTo = "";
                }
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
    */
}
</script>

<style scoped>
</style>
