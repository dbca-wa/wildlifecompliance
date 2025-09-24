<template lang="html">
  <div id="schemaMasterlist">

    <div class="row">
        <div class="col-sm-12">
            <FormSection
                :form-collapse="false"
                label="Schema Masterlist Questions"
            >
                <div class="panel panel-default">
                    <div class="row">
                        <div class="col-md-12">
                            <button class="btn btn-primary float-end" @click.prevent="addTableEntry()" name="add-masterlist">New Question</button>
                        </div>
                    </div>
                    <div class="row"><br/></div> 
                    <div class="row">
                        <div class="col-md-12">
                            <div class="form-group">

                                <datatable ref="schema_masterlist_table"
                                    :id="schema_masterlist_id" 
                                    :dtOptions="dtOptionsSchemaMasterlist"
                                    :dtHeaders="dtHeadersSchemaMasterlist" 
                                />

                            </div>
                        </div>
                    </div>
                </div>
            </FormSection>
        </div>
    </div>

    <modal transition="modal fade" @ok="ok()" title="Schema Masterlist Question" large>
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
                <form class="form-horizontal" name="schema_masterlist">

                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label float-start" >Question</label>
                        </div>
                        <div class="col-md-9">
                            <textarea class="form-control" name="question" v-model="masterlist.question"></textarea>
                        </div>
                    </div>
                    <div class="row"><div class="col-md-12" >&nbsp;</div></div>
                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label float-start" >Answer Type</label>
                        </div>
                        <div class="col-md-6">
                            <select class="form-control" ref="select_answer_type" name="select-answer-type" v-model="masterlist.answer_type">
                                <option v-for="a in answerTypes" :value="a.value" >{{a.label}}</option>
                            </select>     
                        </div>
                    </div>
                    <div class="row"><div class="col-md-12" >&nbsp;</div></div>

                    <div class="row" v-if="showOptions">

                        <SchemaOption  ref="schema_option" :addedOptions="addedOptions" :canAddMore="true" />

                    </div>
                    <div class="row" v-else-if="showTables">

                        <SchemaHeader :addedHeaders="addedHeaders" :answerTypes="answerTypes" :canAddMore="true" />
                        <SchemaExpander :addedExpanders="addedExpanders" :answerTypes="answerTypes" :canAddMore="true" />

                    </div>

                    <div class="row">
                        <div class="col-md-3">
                            <label class="control-label float-start" >Help text url</label>
                        </div>
                        <div class="col-md-9">
                            <textarea class="form-control" name="help_text_url" v-model="masterlist.help_text_url"></textarea>
                        </div>
                    </div>

                </form>
            </div>
        </div>
        <div slot="footer">
            <button type="button" class="btn btn-primary" @click="saveMasterlist()">Save</button>
        </div>
    </modal>

  </div>
</template>

<script>
import { v4 as uuid } from 'uuid';
import datatable from '@vue-utils/datatable.vue'
import modal from '@vue-utils/bootstrap-modal.vue'
import alert from '@vue-utils/alert.vue'
import SchemaOption from './schema_add_option.vue'
import SchemaHeader from './schema_add_header.vue'
import SchemaExpander from './schema_add_expander.vue'
import {
  api_endpoints,
  helpers, fetch_util
}
from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name:'schemaMasterlistModal',
    components: {
        FormSection,
        modal,
        alert,
        datatable,
        SchemaOption,
        SchemaHeader,
        SchemaExpander,
    },
    props:{
    },
    data:function () {
        let vm = this;
        vm.schema_masterlist_url = helpers.add_endpoint_join(api_endpoints.schema_masterlist_paginated, 'schema_masterlist_datatable_list/?format=datatables');
        return {
            schema_masterlist_id: 'schema-materlist-datatable-'+uuid(),
            pMasterListBody: 'pMasterListBody' + uuid(),
            pOptionBody: 'pOptionBody' + uuid(),
            pHeaderBody: 'pHeaderBody' + uuid(),
            pExpanderBody: 'pOptionBody' + uuid(),
            filterOptions: '',
            isModalOpen:false,
            missing_fields: [],
            // masterlist table
            dtHeadersSchemaMasterlist: ["ID", "QuestionOP", "QuestionHD", "QuestionEX", "Question", "Answer Type", "Action"],
            dtOptionsSchemaMasterlist:{
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                serverSide: true,
                autowidth: false,
                processing: true,
                ajax: {
                    "url": vm.schema_masterlist_url, 
                },
                columnDefs: [
                    { visible: false, targets: [ 0, 1, 2, 3, ] } 
                ],
                columns: [
                    { 
                        data: "id",
                    },
                    { 
                        data: "options",
                    },
                    { 
                        data: "headers",
                    },
                    { 
                        data: "expanders",
                    },
                    { 
                        data: "question",
                        width: "80%",
                        mRender:function (data,type,full) {
                            var ellipsis = '...',
                                truncated = _.truncate(data, {
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
                                    text: data
                                });
                            }

                            return result
                        },
                        'createdCell': helpers.dtPopoverCellFn,
                    },
                    { 
                        data: "answer_type",
                        width: "10%",
                    },
                    { 
                        data: "id",
                        width: "10%",
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
                            vm.$refs.schema_masterlist_table.vmDataTable.search( this.value ).draw();
                        }
                    }, 0)));
                }
            },
            masterlist: {
                id: '',
                name: '',
                question: '',
                answer_type: '',
                options: null,
                headers: null,
                expanders: null,
                help_text_url: '',
            },
            answerTypes: [],
            addedHeaders: [],
            addedHeader: {
                label: '',
                value: '',
                colSize: ''
            },
            addedExpanders: [],
            addedExpander: {
                label: '',
                value: '',
            },
            showOptions: false,
            showTables: false,
            addedOptions: [],
            addedOption: {
                id: '',
                label: '',
                value: '',
            },
            isNewEntry: false,
        }

    },
    methods: {
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
        setShowAdditional: function(selected_id) {
            const table = ['expander_table']
            const option = ['radiobuttons', 'checkbox', 'select', 'multi-select']
            const q_type = this.answerTypes.find( t => t.value === selected_id && (table.includes(t.value) || option.includes(t.value)))

            this.showOptions = q_type && option.includes(q_type.value) ? true : false
            this.showTables = q_type && table.includes(q_type.value) ? true : false

            // if (this.showOptions && this.isNewEntry) {
            //     this.addedOption.id = ''
            //     this.addedOption.label = ''
            //     this.addedOption.value = ''
            //     let newOption = Object.assign(this.addedOption)
            //     this.addedOptions.push(newOption);          
            // }
            if (this.showOptions) {
                if(this.isNewEntry){
                    this.addedOption.id = ''
                    this.addedOption.label = ''
                    this.addedOption.value = ''
                    let newOption = Object.assign(this.addedOption)
                    this.addedOptions.push(newOption); 
                }
                else{//if in edit mode but has no options added previously then allow to add options.
                    if(this.addedOptions.length==0){
                        this.addedOption.id = ''
                        this.addedOption.label = ''
                        this.addedOption.value = ''
                        let newOption = Object.assign(this.addedOption)
                        this.addedOptions.push(newOption); 
                    }
                }
                         
            }

            if (this.showTables && this.isNewEntry) {
                let newHeader = Object.assign(this.addedHeader)
                this.addedHeaders.push(newHeader);
                let newExpander = Object.assign(this.addedExpander)
                this.addedExpanders.push(newExpander);           
            }
        },
        addOption: function() {
            this.addedOptions.push(Object.assign(this.addedOption))
        },
        addHeader: function() {
            this.addedHeaders.push(Object.assign(this.addedHeader))
        },
        addExpander: function() {
            this.addedExpanders.push(Object.assign(this.addedExpander))
        },
        close: function() {
            const self = this;

            if (!self.errors) {
                $(this.$refs.select_answer_type).val(null).trigger('change');
                $('.has-error').removeClass('has-error');
                let header_name = 'header-answer-type-0'
                $(`[name='${header_name}]`).removeClass('header-answer-type-0')
                self.addedOptions = [];
                self.addedHeaders = [];
                self.addedExpanders = [];

                self.showOptions = false;
                self.showTables = false;
                self.isModalOpen = false;
            }
        },
        saveMasterlist: async function() {
            const self = this;
            const data = self.masterlist;
            data.options = this.addedOptions;
            data.headers = this.addedHeaders;
            data.expanders = this.addedExpanders;

            if (data.id === '') {

                let request = fetch_util.fetchUrl(api_endpoints.schema_masterlist, {method:'POST', body:JSON.stringify(data)},{
                    emulateJSON:true
                })
                request.then((response) => {
                    self.$refs.schema_masterlist_table.vmDataTable.ajax.reload();
                    self.close();
                }, (error) => {
                    swal.fire(
                        'Save Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            } else {

                let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.schema_masterlist,data.id+'/save_masterlist'), {method:'POST', body:JSON.stringify(data)},{
                        emulateJSON:true,
                })
                request.then((response)=>{
                    self.$refs.schema_masterlist_table.vmDataTable.ajax.reload();
                    self.close();
                },(error)=>{
                    swal.fire(
                        'Save Error',
                        helpers.apiVueResourceError(error),
                        'error'
                    )
                });

            }
            this.isNewEntry = false;
        },
        addTableEntry: function() {
            this.isNewEntry = true;
            this.masterlist.answer_type = '';
            this.masterlist.question = '';
            this.masterlist.id = '';
            this.addedOptions = [];
            this.addedHeaders = [];
            this.addedExpanders = [];
            this.masterlist.help_text_url='';
            this.showOptions = false;
            this.isModalOpen = true;
        },
        initEventListeners: function(){
            const self = this;

            self.$refs.schema_masterlist_table.vmDataTable.on('click','.edit-row', function(e) {
                e.preventDefault();
                self.isNewEntry = false;
                self.$refs.schema_masterlist_table.row_of_data = self.$refs.schema_masterlist_table.vmDataTable.row('#'+$(this).attr('data-rowid'));

                self.masterlist.id = self.$refs.schema_masterlist_table.row_of_data.data().id;
                self.masterlist.answer_type = self.$refs.schema_masterlist_table.row_of_data.data().answer_type;
                self.masterlist.question = self.$refs.schema_masterlist_table.row_of_data.data().question;
                self.addedOptions = self.$refs.schema_masterlist_table.row_of_data.data().options;
                self.addedHeaders = self.$refs.schema_masterlist_table.row_of_data.data().headers;       
                self.addedExpanders = self.$refs.schema_masterlist_table.row_of_data.data().expanders;
                self.masterlist.help_text_url = self.$refs.schema_masterlist_table.row_of_data.data().help_text_url;

                $(self.$refs.select_answer_type).val(self.masterlist.answer_type).trigger('change');
                self.setShowAdditional(self.masterlist.answer_type)
                self.isModalOpen = true;
            });

            self.$refs.schema_masterlist_table.vmDataTable.on('click','.delete-row', function(e) {
                e.preventDefault();
                self.$refs.schema_masterlist_table.row_of_data = self.$refs.schema_masterlist_table.vmDataTable.row('#'+$(this).attr('data-rowid'));
                self.masterlist.id = self.$refs.schema_masterlist_table.row_of_data.data().id;

                swal.fire({
                    title: "Delete Masterlist",
                    text: "Are you sure you want to delete?",
                    icon: "question",
                    showCancelButton: true,
                    confirmButtonText: 'Accept'

                }).then(async (result) => {

                    if (result.ok) {
                        let request = fetch_util.fetchUrl(
                            helpers.add_endpoint_json(api_endpoints.schema_masterlist,(self.masterlist.id+'/delete_masterlist')), {method:"DELETE"}
                        )
                        request.then((response) => {
                            self.$refs.schema_masterlist_table.vmDataTable.ajax.reload();
                        }, (error) => {
                            swal.fire(
                                'Delete Error',
                                helpers.apiVueResourceError(error),
                                'error'
                            )
                        });
                    }

                },(error) => {
                    //
                });                
            });
        },
        initAnswerTypeSelector: function () {
            const self = this;
            $(self.$refs.select_answer_type).select2({
                "theme": "bootstrap-5",
                placeholder:"Select Answer Type..."
            }).
            on("select2:selecting",function (e) {
                let selected = $(e.currentTarget);
            }).
            on("select2:select",function (e) {
                let selected = $(e.currentTarget);
                self.masterlist.answer_type = selected.val()
                self.setShowAdditional(selected.val())
            }).
            on("select2:unselect",function (e) {
                let selected = $(e.currentTarget);
                self.masterlist.answer_type = selected.val()
            });
        },
        initHeaderAnswerTypeSelector: function (index) {
            const self = this;
            let header_name = 'header-answer-type-' + index
            $(`[name='${header_name}]`).select2({
                "theme": "bootstrap-5",
                placeholder:"Select Answer Type..."
            }).
            on("select2:selecting",function (e) {
                let selected = $(e.currentTarget);
            }).
            on("select2:select",function (e) {
                let selected = $(e.currentTarget);
                // self.masterlist.answer_type = selected.val()
                // self.setShowAdditional(selected.val())
            }).
            on("select2:unselect",function (e) {
                let selected = $(e.currentTarget);
                self.masterlist.answer_type = selected.val()
            });
        },
        initSelects: async function() {

            let request = fetch_util.fetchUrl(helpers.add_endpoint_join(api_endpoints.schema_masterlist,'1/get_masterlist_selects'))
            request.then(res=>{

                    this.answerTypes = res.all_answer_types

            }).catch((error) => {
                swal.fire(
                    'Get Application Selects Error',
                    helpers.apiVueResourceError(error),
                    'error'
                )
            });
            this.initAnswerTypeSelector();
        },        
    },
    mounted: function() {
        this.form = document.forms.schema_masterlist;
        this.$nextTick(() => {
            this.initEventListeners();
            this.initSelects();
        });
    }
}
</script>
