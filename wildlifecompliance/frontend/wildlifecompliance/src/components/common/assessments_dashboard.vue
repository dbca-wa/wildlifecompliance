<template id="assessment_dashboard">
    <div class="row">
        <div class="col-sm-12">
            <div class="panel panel-default">
                <div class="panel-heading">
                    <h3 class="panel-title">Applications referred to me
                        <a :href="'#'+pBody" data-toggle="collapse"  data-parent="#userInfo" expanded="true" :aria-controls="pBody">
                            <span class="glyphicon glyphicon-chevron-up pull-right "></span>
                        </a>
                    </h3>
                </div>
                <div class="panel-body collapse in" :id="pBody">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Licence Type</label>
                                <select class="form-control" v-model="filterApplicationLicenceType">
                                    <option value="All">All</option>
                                    <option v-for="lt in application_licence_types" :value="lt" v-bind:key="`licence_type_${lt}`">{{lt}}</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Status</label>
                                <select class="form-control" v-model="filterApplicationStatus">
                                    <option value="All">All</option>
                                    <option v-for="s in application_status" :value="s" v-bind:key="`status_${s.id}`">{{s.name}}</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Submitter</label>
                                <select class="form-control" v-model="filterApplicationSubmitter">
                                    <option value="All">All</option>
                                    <option v-for="s in application_submitters" :value="s.email" v-bind:key="`s_email_${s.email}`">{{s.search_term}}</option>
                                </select>
                            </div>
                        </div>                        
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label for="">Lodged From</label>
                            <div class="input-group date" ref="applicationDateFromPicker">
                                <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterApplicationLodgedFrom">
                                <span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <label for="">Lodged To</label>
                            <div class="input-group date" ref="applicationDateToPicker">
                                <input type="text" class="form-control" placeholder="DD/MM/YYYY" v-model="filterApplicationLodgedTo">
                                <span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>
                            </div>
                        </div>                   
                    </div>
                    <div class="row"><br/></div>             
                    <div class="row">
                        <div class="col-lg-12">
                            <datatable ref="assessment_datatable" :id="datatable_id" :dtOptions="assessment_options" :dtHeaders="assessment_headers"/>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
<script>
import datatable from '@/utils/vue/datatable.vue'
import {
    api_endpoints,
    helpers
}from '@/utils/hooks'
export default {
    name: 'AssessmentTableDash',
    data() {
        let vm = this;
        return {
            pBody: 'pBody' + vm._uid,
            datatable_id: 'assessment-datatable-'+vm._uid,
            // Filters for Applications
            filterApplicationLicenceType: 'All',
            filterApplicationStatus: 'All',
            filterApplicationLodgedFrom: '',
            filterApplicationLodgedTo: '',
            filterApplicationSubmitter: 'All',
            dateFormat: 'DD/MM/YYYY',
            datepickerOptions:{
                format: 'DD/MM/YYYY',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            application_status:[],
            application_licence_types: [],
            application_regions: [],
            application_submitters: [],
            assessment_headers:["Number","Licence Category","Activity","Type","Submitter","Applicant","Status","Lodged on","Action"],
            assessment_options:{
                serverSide: true,
                searchDelay: 1000,
                lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
                order: [
                    [0, 'desc']
                ],
                tableID: 'assessment-datatable-'+vm._uid,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": helpers.add_endpoint_join(api_endpoints.assessment_paginated,'datatable_list/?format=datatables'),
                    "dataSrc": "data",
                    // adding extra GET params for Custom filtering
                    "data": function (d) {
                        d.category_name = vm.filterApplicationLicenceType;
                        d.status = vm.filterApplicationStatus.id;
                        d.submitter = vm.filterApplicationSubmitter;
                        d.date_from = vm.filterApplicationLodgedFrom != '' && vm.filterApplicationLodgedFrom != null ? moment(vm.filterApplicationLodgedFrom, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
                        d.date_to = vm.filterApplicationLodgedTo != '' && vm.filterApplicationLodgedTo != null ? moment(vm.filterApplicationLodgedTo, 'DD/MM/YYYY').format('YYYY-MM-DD'): '';
                    }
                },
                columns: [
                    {
                        data: "application",
                        name: "application__lodgement_number"
                    },
                    {
                        data: "application_category",
                        mRender:function (data,type,full) {
                            return data != '' && data != null ? `${data}` : '';
                        },
                        orderable: false,
                        searchable: false // handled by filter_queryset override method - class AssessmentFilterBackend
                    },
                    {
                        data: "licence_activity",
                        mRender:function (data,type,full) {
                            return data.id != '' && data.id != null ? `${data.name}` : '';
                        },
                        orderable: false,
                        searchable: false // handled by filter_queryset override method - class AssessmentFilterBackend
                    },
                    {
                        data: "application_type",
                        mRender:function (data,type,full) {
                            return data.name;
                        },
                        orderable: false,
                        searchable: false // handled by filter_queryset override method - class AssessmentFilterBackend
                    },
                    {
                        data: "submitter",
                        name: "application__submitter__first_name, application__submitter__last_name, application__submitter__email",
                        mRender:function (data,type,full) {
                            if (data) {
                                return `${data.first_name} ${data.last_name}`;
                            }
                            return ''
                        },
                        orderable: false,
                        searchable: false // handled by filter_queryset override method - class AssessmentFilterBackend
                    },
                    {
                        data: "applicant",
                        orderable: false,
                        searchable: false // handled by filter_queryset override method - class AssessmentFilterBackend
                    },
                    {
                        data: "status",
                        mRender:function (data,type,full) {
                            return data.name;
                        },
                        orderable: false,
                        searchable: false // handled by filter_queryset override method - class AssessmentFilterBackend
                    },
                    {
                        data: "application_lodgement_date",
                        mRender:function (data,type,full) {
                            return data != '' && data != null ? moment(data).format(vm.dateFormat): '';
                        },
                        orderable: false,
                        searchable: false // handled by filter_queryset override method - class AssessmentFilterBackend
                    },
                    {
                        data: "can_be_processed",
                        mRender:function (data,type,full) {
                            let links = '';
                            links +=  full.can_be_processed ? `<a href='/internal/application/assessment/${full.application_id}'>Process</a><br/>`: `<a href='/internal/application/assessment/${full.application_id}'>View</a><br/>`;
                            return links;
                        },
                        orderable: false,
                        searchable: false
                    }
                ],
                processing: true,
                initComplete: function () {
                    // Grab Activity from the data in the table
                    var titleColumn = vm.$refs.assessment_datatable.vmDataTable.columns(vm.getColumnIndex('licence category'));
                    titleColumn.data().unique().sort().each( function ( d, j ) {
                        let activityTitles = [];
                        $.each(d,(index,a) => {
                            a != null && activityTitles.indexOf(a) < 0 && a.length ? activityTitles.push(a): '';
                        })
                        vm.application_licence_types = activityTitles;
                    });
                    // Grab submitters from the data in the table
                    var submittersColumn = vm.$refs.assessment_datatable.vmDataTable.columns(vm.getColumnIndex('submitter'));
                    submittersColumn.data().unique().sort().each( function ( d, j ) {
                        var submitters = [];
                        $.each(d,(index, submitter) => {
                            if (!submitters.find(item => item.email == submitter.email) || submitters.length == 0){
                                submitters.push({
                                    'email':submitter.email,
                                    'search_term': `${submitter.first_name} ${submitter.last_name} (${submitter.email})`
                                });
                            }
                        });
                        vm.application_submitters = submitters;
                    });
                    // Grab Status from the data in the table
                    var statusColumn = vm.$refs.assessment_datatable.vmDataTable.columns(vm.getColumnIndex('status'));
                    statusColumn.data().unique().sort().each( function ( d, j ) {
                        let statusTitles = [];
                        $.each(d,(index,a) => {
                            a != null && !statusTitles.filter(status => status.id == a.id ).length ? statusTitles.push(a): '';
                        })
                        vm.application_status = statusTitles;
                    });
                }
            }
        }
    },
    components:{
        datatable
    },
    watch:{
        filterApplicationActivity: function() {
            let vm = this;
            if (vm.filterApplicationActivity!= 'All') {
                vm.$refs.assessment_datatable.vmDataTable.columns(2).search(vm.filterApplicationActivity).draw();
            } else {
                vm.$refs.assessment_datatable.vmDataTable.columns(2).search('').draw();
            }
        },
        filterApplicationStatus: function() {
            this.filterByColumn('status', this.filterApplicationStatus);
        },
        filterApplicationSubmitter: function(){
            this.$refs.assessment_datatable.vmDataTable.draw();
        },
        filterApplicationLodgedFrom: function(){
            this.$refs.assessment_datatable.vmDataTable.draw();
        },
        filterApplicationLodgedTo: function(){
            this.$refs.assessment_datatable.vmDataTable.draw();
        },
        filterApplicationLicenceType: function(){
            this.filterByColumn('licence category', this.filterApplicationLicenceType);
        },
    },
    computed: {
    },
    methods:{
        addEventListeners: function(){
            let vm = this;
            // Initialise Application Date Filters
            $(vm.$refs.applicationDateToPicker).datetimepicker(vm.datepickerOptions);
            $(vm.$refs.applicationDateToPicker).on('dp.change', function(e){
                if ($(vm.$refs.applicationDateToPicker).data('DateTimePicker').date()) {
                    vm.filterApplicationLodgedTo =  e.date.format('DD/MM/YYYY');
                }
                else if ($(vm.$refs.applicationDateToPicker).data('date') === "") {
                    vm.filterapplicationodgedTo = "";
                }
             });
            $(vm.$refs.applicationDateFromPicker).datetimepicker(vm.datepickerOptions);
            $(vm.$refs.applicationDateFromPicker).on('dp.change',function (e) {
                if ($(vm.$refs.applicationDateFromPicker).data('DateTimePicker').date()) {
                    vm.filterApplicationLodgedFrom = e.date.format('DD/MM/YYYY');
                    $(vm.$refs.applicationDateToPicker).data("DateTimePicker").minDate(e.date);
                }
                else if ($(vm.$refs.applicationDateFromPicker).data('date') === "") {
                    vm.filterApplicationLodgedFrom = "";
                    $(vm.$refs.applicationDateToPicker).data("DateTimePicker").minDate(false);
                }
            });
        },
        initialiseSearch:function(){
            this.submitterSearch();
            this.dateSearch();
        },
        submitterSearch:function(){
            let vm = this;
            vm.$refs.assessment_datatable.table.dataTableExt.afnFiltering.push(
                function(settings,data,dataIndex,original){
                    let filtered_submitter = vm.filterApplicationSubmitter;
                    if (filtered_submitter == 'All'){ return true; } 
                    return filtered_submitter == original.submitter.email;
                }
            );
        },
        dateSearch:function(){
            let vm = this;
            vm.$refs.assessment_datatable.table.dataTableExt.afnFiltering.push(
                function(settings,data,dataIndex,original){
                    let from = vm.filterApplicationLodgedFrom;
                    let to = vm.filterApplicationLodgedTo;
                    let val = original.lodgement_date;
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
        },
        getColumnIndex: function(column_name) {
            return this.assessment_headers.map(header => header.toLowerCase()).indexOf(column_name.toLowerCase());
        },
        filterByColumn: function(column, filterAttribute) {
            const column_idx = this.getColumnIndex(column);
            const filterValue = typeof(filterAttribute) == 'string' ? filterAttribute : filterAttribute.name;
            if (filterValue!= 'All') {
                this.$refs.assessment_datatable.vmDataTable.columns(column_idx).search('^' + filterValue +'$', true, false).draw();
            } else {
                this.$refs.assessment_datatable.vmDataTable.columns(column_idx).search('').draw();
            }
        },
    },
    mounted: function(){
        let vm = this;
        $( 'a[data-toggle="collapse"]' ).on( 'click', function () {
            var chev = $( this ).children()[ 0 ];
            window.setTimeout( function () {
                $( chev ).toggleClass( "glyphicon-chevron-down glyphicon-chevron-up" );
            }, 100 );
        });
        this.$nextTick(() => {
            vm.addEventListeners();
            vm.initialiseSearch();
        });
    }
}
</script>
<style scoped>
</style>