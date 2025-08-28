<template id="application_conditions">     
</template>
<script>
import { v4 as uuid } from 'uuid';
import {
    api_endpoints,
    helpers, fetch_util
}
from '@/utils/hooks';
import '@/scss/dashboards/application.scss';
import datatable from '@vue-utils/datatable.vue';
import ConditionDetail from './application_add_condition.vue';
import { mapActions, mapGetters } from 'vuex'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'InternalApplicationConditions',
    props: {
        activity: {
            type: Object,
            required: true
        }
    },
    data: function() {
        let vm = this;
        return {
            form: null,
            datepickerOptions:{
                format: 'YYYY-MM-DD',
                showClear:true,
                allowInputToggle:true
            },
            panelBody: "application-conditions-"+uuid(),
            viewedCondition: {},
            conditions: [],
            purposes: [],
            condition_headers:["Condition","Purpose","Source","Due Date","Recurrence","Action","Order"],
            condition_options:{
                autoWidth: false,
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": helpers.add_endpoint_join(api_endpoints.applications,this.$store.getters.application.id+'/conditions/?licence_activity='+this.$store.getters.selected_activity_tab_id),
                    "dataSrc": ''
                },
                order: [],
                columns: [
                    {
                        data: "condition",
                        mRender:function (data,type,full) {
                            return data ? data.substring(0, 80) : ''
                        },
                        orderable: false
                    },
                    {
                        data: "purpose_name",
                        orderable: false
                    },
                    {
                        data: "source_name",
                        orderable: false
                    },
                    {
                        data: "due_date",
                        mRender:function (data,type,full) {
                            return data != '' && data != null ? moment(data).format('YYYY-MM-DD'): '';
                        },
                        orderable: false
                    },
                    {
                        data: "recurrence",
                        mRender:function (data,type,full) {
                            if (full.recurrence){
                                switch(full.recurrence_pattern){
                                    case 1:
                                    case "weekly":
                                        return `Once per ${full.recurrence_schedule} week(s)`;
                                    case 2:
                                    case "monthly":
                                        return `Once per ${full.recurrence_schedule} month(s)`;
                                    case 3:
                                    case "yearly":
                                        return `Once per ${full.recurrence_schedule} year(s)`;
                                    default:
                                        return '';
                                }
                            }
                            return '';
                        },
                        orderable: false
                    },
                    {
                        data: "source_group",
                        mRender:function (data,type,full) {
                            let links = '';
                            if(full.source_group && vm.activity.processing_status.id !== 'with_officer_finalisation') {
                                links = `
                                    <a href='#' class="editCondition" data-id="${full.id}">Edit</a><br/>
                                    <a href='#' class="deleteCondition" data-id="${full.id}">Delete</a><br/>
                                `;
                            }
                            if(!full.source_group && vm.canEditConditions) {
                                links = `
                                    <a href='#' class="editCondition" data-id="${full.id}">Edit</a><br/>
                                    <a href='#' class="deleteCondition" data-id="${full.id}">Delete</a><br/>
                                `;
                            }
                            return links;
                        },
                        orderable: false
                    },
                    {
                        data: "id",
                        mRender:function (data,type,full) {
                            let links = '';
                            if(vm.canEditConditions) {
                                links +=  `<a class="dtMoveUp" data-id="${full.id}" href='#'><i class="fa fa-angle-up"></i></a><br/>`;
                                links +=  `<a class="dtMoveDown" data-id="${full.id}" href='#'><i class="fa fa-angle-down"></i></a><br/>`;
                            }
                            return links;
                        },
                        orderable: false
                    }
                ],
                processing: true,
                rowCallback: function ( row, data, index) {
                    if (data.return_type && !data.due_date) {
                        $('td', row).css('background-color', 'Red');
                        vm.setActivityTabWorkflowState({ tab_id: vm.selected_activity_tab_id, bool: true} )
                    }
                },
                drawCallback: function (settings) {
                    if(vm.$refs.conditions_datatable) {
                        $(vm.$refs.conditions_datatable.table).find('tr:last .dtMoveDown').remove();
                        $(vm.$refs.conditions_datatable.table).children('tbody').find('tr:first .dtMoveUp').remove();
                    }
                    // Remove previous binding before adding it
                    $('.dtMoveUp').unbind('click');
                    $('.dtMoveDown').unbind('click');
                    // Bind clicks to functions
                    $('.dtMoveUp').click(vm.moveUp);
                    $('.dtMoveDown').click(vm.moveDown);
                },
                preDrawCallback: function (settings) {
                    vm.setActivityTabWorkflowState({ tab_id: vm.selected_activity_tab_id, bool: false} )
                }
            }
        }
    },
    components: {
        FormSection,
        datatable,
        ConditionDetail
    },
    computed:{
        ...mapGetters([
            'application',
            'selected_activity_tab_id',
            'hasRole',
            'sendToAssessorActivities',
            'canEditAssessmentFor',
            'current_user',
            'canAssignOfficerFor',
        ]),
        canAddConditions: function() {
            if(!this.selected_activity_tab_id || this.activity == null) {
                return false;
            }

            // check activity is not assigned to another officer.
            var selectedActivity = this.application.activities.find(activity => {
                return activity.licence_activity === this.selected_activity_tab_id;
            });

            let required_role = false;
            if (this.activity.processing_status.id === 'with_assessor') {
                let assessment = this.canEditAssessmentFor(this.selected_activity_tab_id)
                required_role = assessment && assessment.assessors.find(assessor => assessor.id === this.current_user.id) ? 'assessor' : false;

            } else if (this.activity.processing_status.id === 'with_officer') {
                required_role =  this.canAssignOfficerFor(this.selected_activity_tab_id) ? 'licensing_officer' : false;
                if (selectedActivity.assigned_officer != null && selectedActivity.assigned_officer !== this.current_user.id) {
                    required_role = false;
                };

            } else if (this.activity.processing_status.id === 'with_officer_conditions') {
                required_role =  this.canAssignOfficerFor(this.selected_activity_tab_id) ? 'licensing_officer' : false;
                if (selectedActivity.assigned_officer != null && selectedActivity.assigned_officer !== this.current_user.id) {
                    required_role = false;
                };
            }

            if (required_role && !['with_assessor', 'with_officer_conditions'].includes(selectedActivity.processing_status.id)) {
                required_role = false;
            }

            return required_role && this.hasRole(required_role, this.selected_activity_tab_id);
        },
        canEditConditions: function() {
            if(!this.selected_activity_tab_id || this.activity == null) {
                return false;
            }

            // check activity is not assigned to another officer.
            var selectedActivity = this.application.activities.find(activity => {
                return activity.licence_activity === this.selected_activity_tab_id;
            });
            if (selectedActivity.assigned_officer != null && selectedActivity.assigned_officer !== this.current_user.id) {
                return false;
            };

            let required_role = false;
            switch(this.activity.processing_status.id) {
                case 'with_assessor':
                    required_role = false;  // only assessors in same group for added condition row can edit.
                break;
                case 'with_officer_conditions':
                    required_role =  this.canAssignOfficerFor(this.selected_activity_tab_id) ? 'licensing_officer' : false;
                break;
            }

            if (selectedActivity.processing_status.id !== 'with_officer_conditions') {
                required_role = false;
            }

            return required_role && this.hasRole(required_role, this.selected_activity_tab_id);
        },    
        isLicensingOfficer: function() {
            return this.hasRole('licensing_officer', this.selected_activity_tab_id);
        },
    },
    methods:{
        ...mapActions([
            'setActivityTabWorkflowState',
        ]),
        addCondition(preloadedCondition){
            var showDueDate = false
            if(preloadedCondition) {
                this.viewedCondition = preloadedCondition;
                this.viewedCondition.due_date = preloadedCondition.due_date != null ? moment(preloadedCondition.due_date).format('YYYY-MM-DD'): '';
                showDueDate=this.viewedCondition.require_return
            }
            else {
                this.viewedCondition = {
                    standard: true,
                    recurrence: false,
                    due_date: '',
                    free_condition: '',
                    recurrence_pattern: 'weekly',
                    application: this.application.id
                };
            }
            this.$refs.condition_detail.showDueDate = showDueDate
            this.$refs.condition_detail.licence_activity = this.selected_activity_tab_id;
            this.$refs.condition_detail.isModalOpen = true;
        },
        removeCondition(_id){
            let vm = this;
            swal.fire({
                title: "Remove Condition",
                text: "Are you sure you want to remove this condition?",
                type: "warning",
                showCancelButton: true,
                confirmButtonText: 'Remove Condition',
                confirmButtonColor:'#d9534f'
            }).then((result) => {
                if (result) {
                    let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.application_conditions,_id+'/delete'), {method:"DELETE"})
                    request.then((response) => {
                        vm.$refs.conditions_datatable.vmDataTable.ajax.reload();
                    }, (error) => {
                        console.log(error);
                    });
                }
            },(error) => {
            });
        },
        async fetchConditions(){
            let vm = this;
            let request = fetch_util.fetchUrl(api_endpoints.application_standard_conditions)
            request.then((response) => {
                vm.conditions = response
            }).catch((error) => {
                console.log(error);
            })
        },
        fetchPurposes(){
            this.purposes = [];
            var selectedActivity = this.application.activities.find(activity => {
                return activity.licence_activity === this.selected_activity_tab_id;
            });
            this.purposes = selectedActivity.purposes;
        },
        async editCondition(_id){
            let vm = this;
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.application_conditions,_id))
            request.then((response) => {
                response.standard ? $(this.$refs.condition_detail.$refs.standard_req).val(response.standard_condition).trigger('change'): '';
                this.addCondition(response);
            }).catch((error) => {
                console.log(error);
            })
        },
        updatedConditions(){
            if (this.$refs.conditions_datatable !== undefined && this.$refs.conditions_datatable.vmDataTable){
                this.$refs.conditions_datatable.vmDataTable.ajax.reload();            
            }
            // this.$refs.conditions_datatable.vmDataTable.ajax.reload();
        },
        eventListeners(){
            let vm = this;
            if (vm.$refs.conditions_datatable==null){
                return
            }
            vm.$refs.conditions_datatable.vmDataTable.on('click', '.deleteCondition', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.removeCondition(id);
            });
            vm.$refs.conditions_datatable.vmDataTable.on('click', '.editCondition', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.editCondition(id);
            });
            vm.$refs.conditions_datatable.vmDataTable.on('click', '.dtMoveUp', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.moveUp(e);
            });
            vm.$refs.conditions_datatable.vmDataTable.on('click', '.dtMoveDown', function(e) {
                e.preventDefault();
                var id = $(this).attr('data-id');
                vm.moveDown(e);
            });
        },
        async sendDirection(req,direction){
            let movement = direction == 'down'? 'move_down': 'move_up';
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.application_conditions,req+'/'+movement))
            request.then((response) => {
            }).catch((error) => {
                console.log(error); 
            })
        },
        async moveUp(e) {
            // Move the row up
            let vm = this;
            e.preventDefault();
            var tr = $(e.target).parents('tr');
            if (await vm.moveRow(tr, 'up', $(e.target).parent().data('id'))){
                await vm.sendDirection($(e.target).parent().data('id'),'up');
            }
        },
        async moveDown(e) {
            // Move the row down
            e.preventDefault();
            let vm = this;
            var tr = $(e.target).parents('tr');
            if (await vm.moveRow(tr, 'down', $(e.target).parent().data('id'))){
                await vm.sendDirection($(e.target).parent().data('id'),'down');
            }
        },
        async moveRow(row, direction, id) {
            // Move up or down (depending...)
            const table = this.$refs.conditions_datatable.vmDataTable;

            let data = table.data()
            let index = -1
            for (let i=0; i<data.length; i++){
                if (data[i].id == id) {
                    if ((direction === 'down' && i+1 === table.data().length) || direction === 'up' && i === 0) {
                        return false
                    }
                    index = i;
                    break;
                }
            }
            
            let order = -1;
            if (direction === 'down') {
              order = 1;
            }
            let new_index = index + order
            if (new_index<0){
                new_index = 1
            }
            if (new_index>table.data().length-1){
                new_index = table.data().length-2
            }
            let selected = table.rows(index).data();
            let replaced = table.rows(new_index).data();
            order = selected.order
            selected.order = replaced.order;
            replaced.order = order;
            let old_data = table.data()
            let new_data = table.data()
            for (let i=0; i<old_data.length; i++){
                if (i===new_index){
                    new_data[i] = selected[0]
                    continue
                }
                if (i===index){
                    new_data[i] = replaced[0]
                    continue
                }
                new_data[i] = old_data[i]
            }
            table.clear()
            table.rows.add(new_data)
            table.draw();
            return true
        },
    },
    mounted: function(){
        this.fetchConditions();
        this.fetchPurposes();
        this.$nextTick(() => {
            this.eventListeners();
            this.form = document.forms.assessment_form;
        });
    },
    updated: function() {
        this.$nextTick(() => {
            this.updatedConditions()
        });
    }
}
</script>
