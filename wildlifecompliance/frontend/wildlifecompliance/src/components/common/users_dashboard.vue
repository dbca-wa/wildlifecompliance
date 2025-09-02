<template id="user_dashboard">
    <div class="row">
        <div class="col-sm-12">
            <FormSection
                :form-collapse="false"
                label="People"
                index="people"
                :subtitle=subtitle
            >
                <div class="panel panel-default">
                    <div class="row">
                        <div class="col-md-3">
                            <div class="form-group">
                                <label for="">Character Flagged</label>
                                <select class="form-control" v-model="filterCharacterFlagged">
                                    <option value="All">All</option>
                                    <option v-for="c in character_flagged_options" :value="c">{{c}}</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <label for="">Date of Birth</label>
                            <div class="input-group date" ref="filterDateOfBirthPicker">
                                <input type="date" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateOfBirth">
                                <!--<span class="input-group-addon">
                                    <span class="glyphicon glyphicon-calendar"></span>
                                </span>-->
                            </div>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-lg-12">
                            <datatable ref="user_datatable" :id="datatable_id" :dtOptions="user_options" :dtHeaders="user_headers"/>
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
import { mapActions, mapGetters } from 'vuex'
import {
    api_endpoints,
    helpers
}from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'UserDashTable',
    props: {
        level:{
            type: String,
            required: true,
            validator:function(val) {
                let options = ['internal'];
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
            datatable_id: 'user-datatable-'+uuid(),
            // Filters for Users
            filterCharacterFlagged: 'All',
            character_flagged_options: ['True','False'],
            filterDateOfBirth: '',
            dateFormat: 'YYYY-MM-DD',
            datepickerOptions:{
                format: 'YYYY-MM-DD',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            user_headers:["Title","Given Name(s)","Last Name","Date of Birth","Email","Phone","Mobile","Fax","Character Flagged","Character Comments","Action"],
            user_options:{
                serverSide: true,
                searchDelay: 1000,
                lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
                order: [
                    [4, 'asc']
                ],
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": vm.url,
                    "data": 'data',
                    // adding extra GET params for Custom filtering
                    "data": function (d) {
                        d.character_flagged = vm.filterCharacterFlagged;
                        d.dob = vm.filterDateOfBirth != '' && vm.filterDateOfBirth != null ? moment(vm.filterDateOfBirth, 'YYYY-MM-DD').format('YYYY-MM-DD'): '';
                    }
                },
                columns: [
                    {
                        data: "title",
                        responsivePriority: 10,
                    },
                    {
                        data: "first_name",
                        responsivePriority: 20,
                    },
                    {
                        data: "last_name",
                        responsivePriority: 30,
                    },
                    {
                        data: "dob",
                        responsivePriority: 40,
                        mRender:function (data,type,full) {
                            return data != '' && data != null ? moment(data).format(vm.dateFormat): '';
                        },
                        searchable: false
                    },
                    {data: "email"},
                    {data: "phone_number"},
                    {data: "mobile_number"},
                    {data: "fax_number"},
                    {
                        data: "character_flagged",
                        orderable: false,
                        searchable: false,
                        className: "capitalise"
                    },
                    {data: "character_comments"},
                    {
                        data:"id",
                        responsivePriority: 50,
                        mRender:function(data, type, full){
                            let links = ''
                            links += "<a href='/internal/users/\__ID__\'> Edit</a><br/>";
                            links +=  `<a href='#${full.id}' apply-on-behalf-of='${full.id}'>New Application</a>`;

                            return links.replace(/__ID__/g, data);
                        },
                        orderable: false,
                        searchable: false
                    },
                ],
                processing: true,
                initComplete: function () {
                    // Fix the table rendering columns
                    vm.$refs.user_datatable.vmDataTable.columns.adjust().responsive.recalc();
                }
            }
        }
    },
    components:{
        datatable,
        FormSection
    },
    watch:{
        filterDateOfBirth: function(){
            this.$refs.user_datatable.vmDataTable.draw();
        },
        filterCharacterFlagged: function(){
            this.$refs.user_datatable.vmDataTable.draw();
        },
    },
    computed: {
        is_external: function(){
            return this.level == 'external';
        },
        subtitle: function() {
            if (this.is_external) {
                return "View people details";
            }
            return "";
        }
    },
    methods: {
        ...mapActions([
            'setApplyProxyId',
            'setApplicationWorkflowState',
            'setApplyLicenceSelect',
        ]),
        applyOnBehalfOf:function (user_id) {
            this.setApplyLicenceSelect({licence_select: 'new_licence'});
            this.setApplyProxyId({id: user_id});
            this.setApplicationWorkflowState({bool: true});
            this.$router.push({
                name: "apply_application_licence",
            });
        },
        addEventListeners: function(){
            let vm = this;
            // Apply on behalf of listener
            vm.$refs.user_datatable.vmDataTable.on('click', 'a[apply-on-behalf-of]', function(e) {
                e.preventDefault();
                var id = parseInt($(this).attr('apply-on-behalf-of'));
                vm.applyOnBehalfOf(id);
            });
        },
    },
    mounted: function(){
        let vm = this;
        this.$nextTick(() => {
            vm.addEventListeners();
        });
    }
}
</script>

