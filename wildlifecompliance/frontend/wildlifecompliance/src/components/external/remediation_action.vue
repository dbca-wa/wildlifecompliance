<template lang="html">
    <div class="container">
        <div class="row">
            <h3>Remediation Action: {{ remediation_action.remediation_action_id }}</h3>
            <div class="col-md-4">
            </div>

            <div class="col-md-8"> 
                <div class="row">
                    <div class="container-fluid">
                        <ul id="pills-tab" class="nav nav-pills mb-3" role="tablist">
                            <li class="nav-item">
                                <a 
                                    class="nav-link active"
                                    data-bs-toggle="pill"
                                    role="tab"
                                    :href="'#'+reTab">
                                    Remediation Action
                                </a>
                            </li>
                            <li class="nav-item">
                                <a 
                                    class="nav-link"
                                    data-bs-toggle="pill"
                                    role="tab"
                                    :href="'#'+coTab">
                                    Confirmation
                                </a>
                            </li>
                        </ul>
                        <div id="pills-tabContent" class="tab-content">
                            <div 
                                :id="reTab" 
                                class="tab-pane fade in active show"
                                role="tabpanel"
                            >
                                <FormSection :formCollapse="false" label="Remediation Action" Index="1">
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-4">
                                            <label>Action Required</label>
                                        </div>
                                        <div class="col-sm-6">
                                            {{ remediation_action.action }}
                                        </div>
                                    </div></div>
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-4">
                                            <label>Due Date</label>
                                        </div>
                                        <div class="col-sm-6">
                                            {{ remediation_action.due_date }}
                                        </div>
                                    </div></div>
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-4">
                                            <label>Details of your compliance</label>
                                        </div>
                                        <div class="col-sm-6">
                                            <textarea :readonly="readonlyForm" class="form-control" v-model="remediation_action.action_taken"/>
                                        </div>
                                    </div></div>
                                    <div class="form-group"><div class="row">
                                        <div class="col-sm-4">
                                            <label>Any photographic evidence</label>
                                        </div>
                                        <div class="col-sm-6" v-if="remediation_action">
                                            <filefield v-if="remediation_action.remediationActionDocumentUrl"
                                                       ref="remediation_action_file"
                                                       name="remediation_action-file"
                                                       :documentActionUrl="remediation_action.remediationActionDocumentUrl"
                                                       @update-parent="remediationActionDocumentUploaded"
                                                       :isRepeatable="true"
                                                       :readonly="readonlyForm" />
                                        </div>
                                    </div></div>
                                </FormSection>
                            </div>

                            <div 
                                :id="coTab" 
                                class="tab-pane fade in"
                                role="tabpanel"
                            >
                                <FormSection :formCollapse="false" label="Confirmation" Index="2">

                                </FormSection>
                            </div>

                        </div>
                        <div v-if="canSaveSubmit" class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
                            <div class="navbar-inner">
                                <div class="container">
                                    <p class="float-end" style="margin-top:5px;">
                                        <input type="button" @click.prevent="submit" class="btn btn-primary float-end button-gap" value="Submit"/>
                                        <input type="button" @click.prevent="save" class="btn btn-primary float-end button-gap" value="Save and Continue"/>
                                        <input type="button" @click.prevent="saveExit" class="btn btn-primary float-end button-gap" value="Save and Exit"/>
                                    </p>
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
import { v4 as uuid } from 'uuid';
 "vue";
import FormSection from "@/components/forms/section_toggle.vue";
//import datatable from '@vue-utils/datatable.vue'
//import utils from "@/components/external/utils";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
//import CommsLogs from "@/components/common/comms_logs.vue";
import filefield from '@common-components/compliance_file.vue';


export default {
    name: 'RemediationAction',
    data() {

        return {
            reTab: 'reTab' + uuid(),
            coTab: 'coTab' + uuid(),
        }
    },
    components: {
        FormSection,
        //CommsLogs,
        //datatable,
        filefield,
    },
    created: async function() {
        try {
            if (this.$route.params.remediation_action_id) {
                await this.loadRemediationAction({ remediation_action_id: this.$route.params.remediation_action_id });
            }
        } catch (err) {
            this.processError(err);
        }
    },
    mounted: function() {

    },
    computed: {
        ...mapGetters('remediationActionStore', {
            remediation_action: "remediation_action",
        }),
        readonlyForm: function(){
            return !this.remediation_action.action_taken_editable;
        },
        canSaveSubmit: function() {
            return this.remediation_action.action_taken_editable;
        }
    },
    methods: {
        ...mapActions('remediationActionStore', {
            loadRemediationAction: 'loadRemediationAction',
            saveRemediationAction: 'saveRemediationAction',
            submitRemediationAction: 'submitRemediationAction',
        }),
        remediationActionDocumentUploaded: function() {
            console.log('remediationActionDocumentUploaded');
        },
        saveExit: async function() {
            try {
                await this.saveRemediationAction();
                await swal.fire("Saved", "The record has been saved", "success");
                this.$router.push({ name: 'external-sanction-outcome-dash' });
            } catch (err) {
                this.processError(err);
            }
        },
        save: async function() {
            try {
                await this.saveRemediationAction();
                await swal.fire("Saved", "The record has been saved", "success");
            } catch (err) {
                this.processError(err);
            }
        },
        submit: async function() {
            console.log('submit');
            let user_action = await this.submitRemediationAction();
            this.$router.push({ name: 'external-remediation-action-submit-success', params: { remediation_action_id: this.remediation_action.id, user_action: user_action }});
        },
        processError: async function(err){
            let errorText = '';
            if (err.body.non_field_errors) {
                // When non field errors raised
                for (let i=0; i<err.body.non_field_errors.length; i++){
                    errorText += err.body.non_field_errors[i] + '<br />';
                }
            } else if(Array.isArray(err.body)) {
                // When general errors raised
                for (let i=0; i<err.body.length; i++){
                    errorText += err.body[i] + '<br />';
                }
            } else {
                // When field errors raised
                for (let field_name in err.body){
                    if (err.body.hasOwnProperty(field_name)){
                        errorText += field_name + ':<br />';
                        for (let j=0; j<err.body[field_name].length; j++){
                            errorText += err.body[field_name][j] + '<br />';
                        }
                    }
                }
            }
            await swal.fire("Error", errorText, "error");
        },
    }
}
</script>

<style>
.button-gap {
    margin: 0 0 0 1em;
}

</style>
