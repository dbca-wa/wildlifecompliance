import Vue from 'vue';
import {
    api_endpoints,
    helpers, fetch_util
}
from '@/utils/hooks';
import moment from 'moment';

export const physicalArtifactStore = {
    namespaced: true,
    state: {
        physical_artifact: {
        },
        
    },
    getters: {
        physical_artifact: (state) => state.physical_artifact,
    },
    mutations: {
        updatePhysicalArtifact(state, physical_artifact) {
            state.physical_artifact = {
                ...physical_artifact
            };
            console.log('updatePhysicalArtifact');
            // format artifact_date for vue
            if (state.physical_artifact.artifact_date) {
                state.physical_artifact.artifact_date = moment(state.physical_artifact.artifact_date, 'YYYY-MM-DD').format('YYYY-MM-DD');
            }
            // format artifact time from 24 to 12 hour
            if (state.physical_artifact.artifact_time) {
                state.physical_artifact.artifact_time = moment(state.physical_artifact.artifact_time, 'HH:mm').format('hh:mm A');
            } else if (state.physical_artifact.artifact_time === '') {
                state.physical_artifact.artifact_time = null;
            }
            // format disposal_date for vue
            if (state.physical_artifact.disposal_date) {
                state.physical_artifact.disposal_date = moment(state.physical_artifact.disposal_date, 'YYYY-MM-DD').format('YYYY-MM-DD');
            }
            // default doc implemented in Artifact model/viewset
            let defaultDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.artifact,
                state.physical_artifact.id + "/process_default_document/"
                )
            state.physical_artifact.defaultDocumentUrl = defaultDocumentUrl; 
            // comms log doc implemented in Artifact model/viewset
            let commsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.artifact,
                state.physical_artifact.id + "/process_comms_log_document/"
                )
            state.physical_artifact.commsLogsDocumentUrl = commsLogsDocumentUrl;
            // renderer
            let rendererDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.physical_artifact,
                state.physical_artifact.id + "/process_renderer_document/"
                )
            state.physical_artifact.rendererDocumentUrl = rendererDocumentUrl;
        },
        updateRelatedItems(state, related_items) {
            state.physical_artifact.related_items = related_items;
        },
        updateOfficerId(state, id) {
            state.physical_artifact.officer_id = id;
        },
        updateCustodianId(state, id) {
            state.physical_artifact.custodian_id = id;
        },
        updateTemporaryDocumentCollectionList(state, {temp_doc_id, input_name}) {
            if (!state.physical_artifact.temporary_document_collection_list) {
                state.physical_artifact.temporary_document_collection_list = [];
            }
            state.physical_artifact.temporary_document_collection_list.push(
                {   "temp_doc_id": temp_doc_id,
                    "input_name": input_name,
                }
            );
        },
        updateStatementId(state, statement_id) {
            console.log(statement_id)
            state.physical_artifact.statement_id = statement_id;
        },
        updateUsedWithinCase(state, used_within_case) {
            state.physical_artifact.used_within_case = used_within_case;
        },
        updateSensitiveNonDisclosable(state, sensitive_non_disclosable) {
            state.physical_artifact.sensitive_non_disclosable = sensitive_non_disclosable;
        },
    },
    actions: {
        async loadPhysicalArtifact({ dispatch, commit }, { physical_artifact_id }) {
            try {
                const returnedPhysicalArtifact = await fetch_util.fetchUrl(
                    helpers.add_endpoint_json(
                        api_endpoints.physical_artifact,
                        physical_artifact_id)
                    );

                console.log(returnedPhysicalArtifact)
                commit("updatePhysicalArtifact", returnedPhysicalArtifact);

                for (let form_data_record of returnedPhysicalArtifact.data) {
                    await dispatch("setFormValue", {
                        key: form_data_record.field_name,
                        value: {
                            "value": form_data_record.value,
                            "comment_value": form_data_record.comment,
                            "deficiency_value": form_data_record.deficiency,
                        }
                    }, {
                        root: true
                    });
                }

            } catch (err) {
                console.log(err);
            }
        },
        async savePhysicalArtifact({ dispatch, state, rootGetters }, { create, internal, legal_case_id }) {
            let physicalArtifactId = null;
            let savedPhysicalArtifact = null;
            try {
                let payload = new Object();
                Object.assign(payload, state.physical_artifact);
                console.log(payload);
                // format artifact date for backend save
                if (payload.artifact_date) {
                    payload.artifact_date = moment(payload.artifact_date, 'YYYY-MM-DD').format('YYYY-MM-DD');
                } else if (payload.artifact_date === '') {
                    payload.artifact_date = null;
                }
                // format artifact time to 24 hours
                if (payload.artifact_time) {
                    payload.artifact_time = moment(payload.artifact_time, 'hh:mm A').format('HH:mm');
                } else if (payload.artifact_time === '') {
                    payload.artifact_time = null;
                }
                // format disposal date for backend save
                if (payload.disposal_date) {
                    payload.disposal_date = moment(payload.disposal_date, 'YYYY-MM-DD').format('YYYY-MM-DD');
                } else if (payload.disposal_date === '') {
                    payload.disposal_date = null;
                }
                if (legal_case_id) {
                    payload.legal_case_id = legal_case_id;
                }
                // Renderer data
                /*
                if ((state.physical_artifact.details_schema && state.physical_artifact.details_schema.length) || 
                    (state.physical_artifact.storage_schema && state.physical_artifact.storage_schema.length)) {
                    payload.renderer_data = rootGetters.renderer_form_data;
                }
                */
                payload.renderer_data = rootGetters.renderer_form_data;
                console.log(payload);

                let fetchUrl = null;
                if (create) {
                    fetchUrl = api_endpoints.physical_artifact;
                    savedPhysicalArtifact = await Vue.http.post(fetchUrl, payload);
                } else {
                    fetchUrl = helpers.add_endpoint_join(
                        api_endpoints.physical_artifact,
                        state.physical_artifact.id + '/'
                        )
                    console.log(payload);
                    savedPhysicalArtifact = await fetch_util.fetchUrl(fetchUrl, {method:"PUT",body:JSON.stringify(payload)});
                }
                await dispatch("setPhysicalArtifact", savedPhysicalArtifact.body);
                physicalArtifactId = savedPhysicalArtifact.body.id;

            } catch (err) {
                console.log(err);
                if (internal) {
                    // return "There was an error saving the record";
                    return err;
                } else {
                    await swal.fire("Error", "There was an error saving the record", "error");
                }
            }
            // internal arg used when file upload triggers record creation
            if (internal) {
                // pass
            }
            // update legal_case
            else if (!create) {
                await swal.fire("Saved", "The record has been saved", "success");
            }
        },
        setPhysicalArtifact({ commit, }, physical_artifact) {
            commit("updatePhysicalArtifact", physical_artifact);
        },
        /*
        setPhysicalArtifactLegalId({ commit, }, legal_case_id) {
            commit("updatePhysicalArtifactLegalId", legal_case_id)
        },
        */
        setRelatedItems({ commit }, related_items ) {
            commit("updateRelatedItems", related_items);
        },
        setOfficerId({ commit }, id ) {
            commit("updateOfficerId", id);
        },
        setCustodianId({ commit }, id ) {
            commit("updateCustodianId", id);
        },
        /*
        setTemporaryDocumentCollectionId({ commit }, temp_doc_id) {
            commit("updateTemporaryDocumentCollectionId", temp_doc_id);
        },
        */
        addToTemporaryDocumentCollectionList({ commit }, {temp_doc_id, input_name}) {
            commit("updateTemporaryDocumentCollectionList", {temp_doc_id, input_name});
        },
        setStatementId({ commit }, statement_id) {
            commit("updateStatementId", statement_id);
        },
        setUsedWithinCase({ commit }, used_within_case) {
            commit("updateUsedWithinCase", used_within_case);
        },
        setSensitiveNonDisclosable({ commit }, sensitive_non_disclosable) {
            commit("updateSensitiveNonDisclosable", sensitive_non_disclosable);
        },
    },
};
