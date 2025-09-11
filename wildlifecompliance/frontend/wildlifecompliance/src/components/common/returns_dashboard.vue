<template id="returns_dashboard">
    <div class="row">
        <div class="col-sm-12">
            <FormSection
                :form-collapse="false"
                label="Returns"
                index="returns"
                :subtitle=subtitle
            >
                <div class="panel panel-default">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Status</label>
                                <select class="form-control" v-model="filterReturnStatus">
                                    <option value="All">All</option>
                                    <option v-for="s in return_statusTitles" :value="s" v-bind:key="`return_status_${s}`">{{s}}</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label for="">Due Date From</label>
                            <div class="input-group date" ref="dueDateFromPicker">
                                <input type="date" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDueDateFrom">
                                <!--<span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>-->
                            </div>
                        </div>
                        <div class="col-md-3">
                            <label for="">Due Date To</label>
                            <div class="input-group date" ref="dueDateToPicker">
                                <input type="date" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDueDateTo">
                                <!--<span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>-->
                            </div>
                        </div>
                    </div><br/>
                    <div class="row">
                        <div class="col-lg-12">
                            <datatable ref="return_datatable" :id="datatable_id" :dtOptions="table_options" :dtHeaders="table_headers"/>
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
import {
    api_endpoints,
    helpers,
    fetch_util
}from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'ReturnTableDash',
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
            pBody: 'pBody' + uuid(),
            datatable_id: 'return-datatable-'+uuid(),
            filterReturnStatus: 'All',
            filterDueDateFrom: '',
            filterDueDateTo: '',
            dateFormat: 'YYYY-MM-DD',
            datepickerOptions:{
                format: 'YYYY-MM-DD',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            return_statusTitles : [],
            table_headers:["Number","Due Date","Status","Licence","Action"],
            table_options:{
                serverSide: true,
                order: [
                    [0, 'desc']
                ],
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": vm.url,
                    "dataSrc": 'data',
                    "data": function (d) {
                        d.status = vm.filterReturnStatus;
                        d.date_from = vm.filterDueDateFrom != '' && vm.filterDueDateFrom != null ? moment(vm.filterDueDateFrom, 'YYYY-MM-DD').format('YYYY-MM-DD'): '';
                        d.date_to = vm.filterDueDateTo != '' && vm.filterDueDateTo != null ? moment(vm.filterDueDateTo, 'YYYY-MM-DD').format('YYYY-MM-DD'): '';
                    }
                },
                columns: [
                    {
                        data: "lodgement_number",
                        mRender:function (data,type,full) {
                            return data;
                        }
                    },
                                        
                    {
                        data: "due_date",
                        mRender:function (data,type,full) {
                            return data != '' && data != null ? moment(data).format(vm.dateFormat): '';
                        }
                    },
                    {   
                        data: "processing_status",
                        mRender:function (data,type,full) {
                            return vm.is_external ? full.customer_status : full.processing_status;
                        },
                        searchable: false                       
                    },
                    {
                        data: "licence",
                        mRender:function (data,type,full) {
                            return full.licence;
                        },
                        searchable: false
                    },
                    {
                        data: "can_be_processed",
                        mRender:function (data,type,full) {
                            let links = '';
                            if (!vm.is_external){       
                                links += (full.can_be_processed && full.user_in_officers) ?
                                    `<a href='/internal/return/${full.id}'>Process</a><br/>` : `<a href='/internal/return/${full.id}'>View</a><br/>`;
            
                                if (['paid','partially_paid'].includes(full.payment_status)){
                                    links +=  `<a href='${full.all_payments_url}' target='_blank' >View Payment</a><br/>`;
                                }
                            }        
                            else{
                                links += (full.can_current_user_edit) ?
                                    `<a href='/external/return/${full.id}'>Continue</a><br/>` : `<a href='/external/return/${full.id}'>View</a><br/>`;                
                            }
                            return links;
                        },
                        searchable: false,
                        orderable: false
                    },
                ],
                processing: true,
                initComplete: function () {
                    var $searchInput = $('div.dataTables_filter input');
                    $searchInput.unbind('keyup search input');
                    $searchInput.bind('keypress', (vm.delay(function(e) {
                        if (e.which == 13) {
                            vm.$refs.return_datatable.vmDataTable.search( this.value ).draw();
                        }
                    }, 0)));
                }
            }
        }
    },
    components:{
        datatable,
        FormSection
    },
    watch:{
        filterReturnStatus: function(value){
            let table = this.$refs.return_datatable.vmDataTable
            value = value != 'All' ? value : ''
            table.column(2).search(value).draw();
        },
        filterDueDateFrom: function(value){
            this.visibleDatatable.vmDataTable.draw();
        },
        filterDueDateTo: function(value){
            this.visibleDatatable.vmDataTable.draw();
        },
    },
    computed: {
        is_external: function(){
            return this.level == 'external';
        },
        visibleDatatable: function() {
            return this.$refs.return_datatable;
        },
        subtitle: function() {
            if (this.is_external) {
                return "View submitted returns and submit new ones";
            }
            return "";
        }
    },
    methods:{
        delay(callback, ms) {
            var timer = 0;
            return function () {
                var context = this, args = arguments;
                clearTimeout(timer);
                timer = setTimeout(function () {
                    callback.apply(context, args);
                }, ms || 0);
            };
        },
        initialiseSearch:function(){
            this.dateSearch();
            let request = fetch_util.fetchUrl(helpers.add_endpoint_join(api_endpoints.returns,'1/get_return_selects'))
            request.then(res=>{
                this.return_statusTitles = res.all_status
            }).catch((error) => {
                console.log(error)
                swal.fire(
                    'Get Return Selects Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        },
        dateSearch:function(){
            let vm = this;
            vm.$refs.return_datatable.table.dataTableExt.afnFiltering.push(
                 function(settings,data,dataIndex,original){
                     let from = vm.filterDueDateFrom;
                     let to = vm.filterDueDateTo;
                     let val = original.due_date;

                     if ( from == '' && to == ''){
                         return true;
                     }
                     else if (from != '' && to != ''){
                         return val != null && val != '' ? moment().range(moment(from,vm.dateFormat),moment(to,vm.dateFormat)).contains(moment(val)) :false;
                     }
                     else if(from == '' && to != ''){
                         if (val != null && val != ''){
                             return moment(to,vm.dateFormat).diff(moment(val)) >= 0 ? true : false;
                         }
                         else{
                             return false;
                         }
                     }
                     else if (to == '' && from != ''){
                         if (val != null && val != ''){
                            return moment(val).diff(moment(from,vm.dateFormat)) >= 0 ? true : false;
                         }
                         else{
                             return false;
                         }
                     }
                     else{
                         return false;
                     }
                 }
            );
        }
    },
    mounted: function(){
        let vm = this;
        this.$nextTick(() => {
            vm.initialiseSearch();
        });
    }
}
</script>