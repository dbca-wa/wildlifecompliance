<template id="sanction_outcome_person_org_dashboard">
    <div class="row">
        <div class="col-sm-12">
            <FormSection
                :form-collapse="false"
                label="Sanction Outcomes"
                index="sanction_outcomes"
            >
                <div class="panel panel-default">
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
import datatable from '@/utils/vue/datatable.vue'
import { api_endpoints, helpers, cache_helper } from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
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

            pBody: 'pBody' + uuid(),
            datatable_id: 'return-datatable-'+uuid(),
            /*
            filterType: 'all',
            filterStatus: 'all',
            filterPaymentStatus: 'all',
            filterDateFrom: '',
            filterDateTo: '',
            */
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
}
</script>