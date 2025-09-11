<template lang="html">
  <div id="schema-group">

    <div class="row">
        <div class="col-sm-12">
            <FormSection
                :form-collapse="false"
                label="Schema Section Groups"
            >
                <div class="panel panel-default">
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="">Licence Purpose</label>
                                <select class="form-control" v-model="filterTablePurpose" >
                                    <option value="All">All</option>
                                    <option v-for="(p, pid) in schemaPurposes" :value="p.value" v-bind:key="`group_${pid}`">{{p.label}}</option>
                                </select>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <button class="btn btn-primary float-end" @click.prevent="addTableEntry()" name="add_group">New Group</button>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="form-group">
                                <label for="">Section</label>
                                <select class="form-control" v-model="filterTableSection" >
                                    <option value="All">All</option>
                                    <option v-for="(s, sid) in schemaSections" :value="s.value" v-bind:key="`section_${sid}`">{{s.label}}</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="row"><br/></div> 
                    <div class="row">
                        <div class="col-md-12">
                            <div class="form-group">

                                <datatable ref="schema_group_table"
                                    :id="schema_group_id" 
                                    :dtOptions="dtOptionsSchemaGroup"
                                    :dtHeaders="dtHeadersSchemaGroup" 
                                />

                            </div>
                        </div>
                    </div>
                </div>

            </FormSection>
        </div>
    </div>

    <modal transition="modal fade" @ok="ok()" title="Schema Section Group" large>
        <div class="container-fluid">
            <div id="error" v-if="missing_fields.length > 0" style="margin: 10px; padding: 5px; color: red; border:1px solid red;">
                <b>Please answer the following mandatory question(s):</b>
                <ul>
                    <li v-for="error in missing_fields">
                        {{ error.label }}
                    </li>
                </ul>
            </div>
            <div>
                <form class="form-horizontal" name="schema_group">

                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label float-start" >Licence Purpose</label>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" ref="select_purpose" name="select-purpose" v-model="filterGroupSection" >
                                <option value="All">Select...</option>
                                <option v-for="(p, pid) in schemaPurposes" :value="p.value" v-bind:key="`purpose_${pid}`">{{p.label}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">&nbsp; </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label float-start" >Section</label>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" ref="select_section" name="select-section" v-model="sectionGroup.section" >
                                <option value="All">Select...</option>
                                <option v-for="(s, sid) in schemaSections" :value="s.value" v-bind:key="`section_${sid}`">{{s.label}}</option>
                            </select>                            
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-md-12">&nbsp; </div>
                    </div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label float-start" >Group Label</label>
                        </div>
                        <div class="col-md-6">
                            <input type="text" class="form-control" v-model="sectionGroup.group_label"/>
                        </div>
                    </div>
                    <div class="row"><div class="col-md-12" >&nbsp;</div></div>
                    <div class="row">
                        <div class="col-md-6">
                            <input type="checkbox" :value="true" v-model="getCheckedRepeatable('isRepeatable').isChecked" >&nbsp;&nbsp;&nbsp;<label>isRepeatable</label></input>
                        </div>
                    </div>
                </form>
            </div>
        </div>
        <div slot="footer">
            <button type="button" class="btn btn-primary" @click="saveGroup">Save</button>
        </div>
    </modal>

  </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import datatable from '@vue-utils/datatable.vue'
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import {
  api_endpoints,
  helpers, fetch_util
}
from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name:'schema-group',
    components: {
        FormSection,
        modal,
        alert,
        datatable,
    },
    props:{
    },
    watch:{
        filterTablePurpose: function() {
            this.$refs.schema_group_table.vmDataTable.draw();
        },
        filterTableSection: function() {
            this.$refs.schema_group_table.vmDataTable.draw();
        },
        filterGroupSection: function() {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.schema_group,'1/get_group_sections'),{
                params: { licence_purpose_id: this.filterGroupSection },
            }).then((res)=>{
                this.schemaSections = res.group_sections;
            }).catch((error) => {
                console.log(error);
            });
        },
    },
    data:function () {
        let vm = this;
        vm.schema_group_url = helpers.add_endpoint_join(api_endpoints.schema_group_paginated, 'schema_group_datatable_list/?format=datatables');
        return {
            schema_group_id: 'schema-group-datatable-'+uuid(),
            pGroupBody: 'pGroupBody' + uuid(),
            isModalOpen:false,
            missing_fields: [],
            filterTablePurpose: 'All',
            filterTableSection: 'All',
            filterGroupSection: 'All',
            dtHeadersSchemaGroup: ["ID", "Licence Purpose", "Section Label", "Group Label", "Action"],
            dtOptionsSchemaGroup:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                searchDelay: 1000,
                responsive: true,
                serverSide: true,
                autowidth: false,
                processing: true,
                ajax: {
                    "url": vm.schema_group_url,
                    "dataSrc": 'data',
                    "data": function (d) {
                        d.licence_purpose_id = vm.filterTablePurpose;
                        d.section_id = vm.filterTableSection;
                    }
                },
                columnDefs: [
                    { visible: false, targets: [ 0 ] } 
                ],
                columns: [
                    { 
                        data: "id",
                        width: "10%",
                        searchable: false,
                    },
                    { 
                        data: "licence_purpose",
                        width: "20%",
                        searchable: false,
                        mRender:function (data,type,full) {
                            return data.name;
                        }
                    },
                    { 
                        data: "section",
                        width: "20%",
                        searchable: false,
                        mRender:function (data,type,full) {
                            return data.section_label;
                        }
                    },
                    { 
                        data: "group_label",
                        width: "60%",
                        searchable: false,
                    },
                    { 
                        data: "id",
                        width: "10%",
                        searchable: false,
                        mRender:function (data,type,full) {
                            var column = `<a class="edit-row" data-rowid=\"__ROWID__\">Edit</a><br/>`;
                            column += `<a class="delete-row" data-rowid=\"__ROWID__\">Delete</a><br/>`;
                            return column.replace(/__ROWID__/g, full.id);
                        }
                    },
                ],
                rowId: function(_data) {
                    return _data.id
                },
                initComplete: function () {
                    var $searchInput = $('div.dataTables_filter input');
                    $searchInput.unbind('keyup search input');
                    $searchInput.bind('keypress', (vm.delay(function(e) {
                        if (e.which == 13) {
                            vm.$refs.schema_group_table.vmDataTable.search( this.value ).draw();
                        }
                    }, 0)));
                }
            },
            licence_purpose: '',
            schemaPurposes: [],
            schemaSections: [],
            sectionGroup: {
                id: '',
                group_name: '',
                group_label: '',
                section: 'All',
                repeatable: false,
            },
            checkedRepeatable: [{
                id: null,
                isChecked: false,
            }],
        }

    },
    computed: {
    },
    methods: {
        getCheckedRepeatable: function(anID, set_checked=false){
            let checked = this.checkedRepeatable.find(r => {return r.id==anID})
            if (!checked) {
                checked = {
                    id: anID,
                    isChecked: set_checked,
                }
                if (['isRepeatable',].includes(anID)){
                    this.checkedRepeatable.push(checked)
                }
            }
            return checked;
        },
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
        close: function() {
            const self = this;

            if (!self.errors) {

                self.isModalOpen = false;
            }
        },
        saveGroup: async function() {
            const self = this;
            const data = self.sectionGroup;

            data.repeatable = false;
            if (self.checkedRepeatable.length>0){
                self.checkedRepeatable.filter( r => {
                    if (r.isChecked) {
                        data.repeatable = true;
                    }
                    return
                })
            }

            if (data.id === '') {

                let request = fetch_util.fetchUrl(api_endpoints.schema_group, {method:'POST', body:JSON.stringify(data)},{
                    emulateJSON:true

                })
                request.then((response) => {

                    self.$refs.schema_group_table.vmDataTable.ajax.reload();
                    self.close();

                }, (error) => {
                    swal.fire(
                        'Save Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            } else {

                let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.schema_group,data.id+'/save_group'), {method:'POST', body:JSON.stringify(data)},{
                        emulateJSON:true,

                })
                request.then((response)=>{

                    self.$refs.schema_group_table.vmDataTable.ajax.reload();
                    self.close();

                },(error)=>{
                    swal.fire(
                        'Save Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            }

        },
        cancel: function() {
            const self = this;
            self.isModalOpen = false;
        },
        addTableEntry: function() {
            this.licence_purpose = '';

            this.sectionGroup.id = '';
            this.sectionGroup.group_name = '';
            this.sectionGroup.group_label = '';
            this.sectionGroup.section = 'All';
            this.sectionGroup.repeatable = false;
            this.checkedRepeatable = [];

            this.isModalOpen = true;
        },
        initEventListeners: function(){
            const self = this;

            self.$refs.schema_group_table.vmDataTable.on('click','.edit-row', function(e) {
                e.preventDefault();
                self.$refs.schema_group_table.row_of_data = self.$refs.schema_group_table.vmDataTable.row('#'+$(this).attr('data-rowid'));

                self.sectionGroup.id = self.$refs.schema_group_table.row_of_data.data().id;
                self.sectionGroup.section = self.$refs.schema_group_table.row_of_data.data().section.id;
                self.sectionGroup.group_label = self.$refs.schema_group_table.row_of_data.data().group_label;
                self.filterGroupSection = self.$refs.schema_group_table.row_of_data.data().licence_purpose.id;

                self.sectionGroup.repeatable = self.$refs.schema_group_table.row_of_data.data().repeatable
                self.checkedRepeatable = []
                self.getCheckedRepeatable('isRepeatable', self.sectionGroup.repeatable);

                self.isModalOpen = true;
            });

            self.$refs.schema_group_table.vmDataTable.on('click','.delete-row', function(e) {
                e.preventDefault();
                self.$refs.schema_group_table.row_of_data = self.$refs.schema_group_table.vmDataTable.row('#'+$(this).attr('data-rowid'));
                self.sectionGroup.id = self.$refs.schema_group_table.row_of_data.data().id;

                swal.fire({
                    title: "Delete Section Group",
                    text: "Are you sure you want to delete?",
                    type: "question",
                    showCancelButton: true,
                    confirmButtonText: 'Accept'

                }).then(async (result) => {

                    if (result) {

                        let request = fetch_util.fetchUrl(
                            helpers.add_endpoint_json(api_endpoints.schema_group,(self.sectionGroup.id+'/delete_group')), {method:"DELETE"}
                        )
    
                        request.then((response) => {

                            self.$refs.schema_group_table.vmDataTable.ajax.reload();

                        }, (error) => {

                        });
    
                    }

                },(error) => {

                });                
            });
        },
        initSelects: async function() {

            let request = fetch_util.fetchUrl(helpers.add_endpoint_join(api_endpoints.schema_group,'1/get_group_selects'))
            request.then(res=>{

                    this.schemaPurposes = res.all_purpose
                    this.schemaSections = res.all_section

            }).catch((error) => {

                swal.fire(
                    'Get Application Selects Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
        },
    },
    mounted: function() {
        this.form = document.forms.schema_group;
        this.$nextTick(() => {
            this.initEventListeners();
            this.initSelects();
        });
    }
}
</script>
