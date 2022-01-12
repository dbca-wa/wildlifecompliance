import Vue from 'vue';
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks';
import moment from 'moment';

export const documentArtifactStore = {
    namespaced: true,
    state: {
        document_artifact: {
        },
        
    },
    getters: {
        document_artifact: (state) => state.document_artifact,
    },
    mutations: {
        updateDocumentArtifact(state, document_artifact) {
            Vue.set(state, 'document_artifact', {
                ...document_artifact
            });
            // format artifact_date for vue
            if (state.document_artifact.artifact_date) {
                state.document_artifact.artifact_date = moment(state.document_artifact.artifact_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            // format artifact time from 24 to 12 hour
            if (state.document_artifact.artifact_time) {
                state.document_artifact.artifact_time = moment(state.document_artifact.artifact_time, 'HH:mm').format('hh:mm A');
            } else if (state.document_artifact.artifact_time === '') {
                state.document_artifact.artifact_time = null;
            }
            /*
            console.log('updateDocumentArtifact');
            if (state.document_artifact.artifact_date) {
                state.document_artifact.artifact_date = moment(state.document_artifact.artifact_date, 'YYYY-MM-DD').format('DD/MM/YYYY');
            }
            */
            // default doc implemented in Artifact model/viewset
            let defaultDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.artifact,
                state.document_artifact.id + "/process_default_document/"
                )
            Vue.set(state.document_artifact, 'defaultDocumentUrl', defaultDocumentUrl); 
            // comms log doc implemented in Artifact model/viewset
            let commsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.artifact,
                state.document_artifact.id + "/process_comms_log_document/"
                )
            Vue.set(state.document_artifact, 'commsLogsDocumentUrl', commsLogsDocumentUrl); 
            /*
            let createLegalCaseProcessCommsLogsDocumentUrl = helpers.add_endpoint_join(
                api_endpoints.legal_case,
                state.legal_case.id + "/create_legal_case_process_comms_log_document/"
                )
            Vue.set(state.legal_case, 'createLegalCaseProcessCommsLogsDocumentUrl', createLegalCaseProcessCommsLogsDocumentUrl);
            */
        },
        updateRelatedItems(state, related_items) {
            Vue.set(state.document_artifact, 'related_items', related_items);
        },
        updatePersonProvidingStatementId(state, person_providing_statement_id) {
            Vue.set(state.document_artifact, 'person_providing_statement_id', person_providing_statement_id);
        },
        updateInterviewerEmail(state, email) {
            Vue.set(state.document_artifact, 'interviewer_email', email);
        },
        updateTemporaryDocumentCollectionId(state, temp_doc_id) {
            Vue.set(state.document_artifact, 'temporary_document_collection_id', temp_doc_id);
        },
        updateOffenderId(state, offender_id) {
            Vue.set(state.document_artifact, 'offender_id', offender_id);
        },
        updateOfficerInterviewer(state, officer_interviewer) {
            console.log(officer_interviewer)
            let officerInterviewerConcise = {}
            officerInterviewerConcise.email = officer_interviewer.email
            officerInterviewerConcise.given_name = officer_interviewer.given_name
            officerInterviewerConcise.surname = officer_interviewer.surname
            Vue.set(state.document_artifact, 'officer_interviewer', officerInterviewerConcise);
        },
        updateOfficerInterviewerId(state, officer_interviewer_id) {
            Vue.set(state.document_artifact, 'officer_interviewer_id', officer_interviewer_id);
        },
        updateErrorMessage(state, errorMessage) {
            Vue.set(state.document_artifact, 'error_message', errorMessage);
        },
        /*
        updateDocumentArtifactLegalId(state, legal_case_id) {
            console.log(legal_case_id)
            Vue.set(state.document_artifact, 'legal_case_id', legal_case_id);
        },
        */
    },
    actions: {
        async loadDocumentArtifact({ dispatch, commit }, { document_artifact_id }) {
            try {
                const returnedDocumentArtifact = await Vue.http.get(
                    helpers.add_endpoint_json(
                        api_endpoints.document_artifact,
                        document_artifact_id)
                    );

                console.log(returnedDocumentArtifact)
                commit("updateDocumentArtifact", returnedDocumentArtifact.body);

            } catch (err) {
                console.log(err);
            }
        },
        async saveDocumentArtifact({ commit, dispatch, state, rootGetters }, { create, internal, legal_case_id }) {
            commit("updateErrorMessage", "");
            let documentArtifactId = null;
            let savedDocumentArtifact = null;
            try {
                let payload = new Object();
                Object.assign(payload, state.document_artifact);
                console.log(payload);
                /*
                if (payload.artifact_date) {
                    payload.artifact_date = moment(payload.artifact_date, 'DD/MM/YYYY').format('YYYY-MM-DD');
                } else if (payload.artifact_date === '') {
                    payload.artifact_date = null;
                }
                */
                // format artifact date for backend save
                if (payload.artifact_date) {
                    payload.artifact_date = moment(payload.artifact_date, 'DD/MM/YYYY').format('YYYY-MM-DD');
                } else if (payload.artifact_date === '') {
                    payload.artifact_date = null;
                }
                // format artifact time to 24 hours
                if (payload.artifact_time) {
                    payload.artifact_time = moment(payload.artifact_time, 'hh:mm A').format('HH:mm');
                } else if (payload.artifact_time === '') {
                    payload.artifact_time = null;
                }

                if (legal_case_id) {
                    payload.legal_case_id = legal_case_id;
                }

                let fetchUrl = null;
                if (create) {
                    fetchUrl = api_endpoints.document_artifact;
                    savedDocumentArtifact = await Vue.http.post(fetchUrl, payload);
                } else {
                    fetchUrl = helpers.add_endpoint_join(
                        api_endpoints.document_artifact,
                        state.document_artifact.id + '/'
                        )
                    //console.log(payload);
                    savedDocumentArtifact = await Vue.http.put(fetchUrl, payload);
                }
                await dispatch("setDocumentArtifact", savedDocumentArtifact.body);
                documentArtifactId = savedDocumentArtifact.body.id;

            } catch (err) {
                console.log(err);
                if (internal) {
                    // return "There was an error saving the record";
                    return err;
                } else {
                    let errorMessage = ''
                    if (err.statusText && err.data && err.data.non_field_errors && err.data.non_field_errors.length > 0) {
                        //await swal("Error", err.data.non_field_errors[0], "error");
                        errorMessage = err.data.non_field_errors[0];
                    } else if (err.bodyText) {
                        //await swal("Error", err.data.non_field_errors[0], "error");
                        errorMessage = err.bodyText;
                    } else {
                        //await swal("Error", "There was an error saving the record", "error");
                        errorMessage = "There was an error saving the record";
                    }
                    commit("updateErrorMessage", errorMessage);
                    await swal("Error", errorMessage, "error");
                }
            }
            // internal arg used when file upload triggers record creation
            if (internal) {
                // pass
            }
            // update legal_case
            else if (!create && !state.document_artifact.error_message) {
                await swal("Saved", "The record has been saved", "success");
            }
        },
        setDocumentArtifact({ commit, }, document_artifact) {
            commit("updateDocumentArtifact", document_artifact);
        },
        /*
        setDocumentArtifactLegalId({ commit, }, legal_case_id) {
            commit("updateDocumentArtifactLegalId", legal_case_id)
        },
        */
        setRelatedItems({ commit }, related_items ) {
            commit("updateRelatedItems", related_items);
        },
        setPersonProvidingStatementId({ commit }, person_providing_statement_id ) {
            commit("updatePersonProvidingStatementId", person_providing_statement_id);
        },
        setInterviewerEmail({ commit }, email ) {
            commit("updateInterviewerEmail", email);
        },
        setTemporaryDocumentCollectionId({ commit }, temp_doc_id) {
            commit("updateTemporaryDocumentCollectionId", temp_doc_id);
        },
        setOffenderId({ commit }, offender_id) {
            commit("updateOffenderId", offender_id);
        },
        setOfficerInterviewer({ commit }, officer_interviewer) {
            console.log(officer_interviewer)
            commit("updateOfficerInterviewer", officer_interviewer);
        },
        setOfficerInterviewerId({ commit }, officer_interviewer_id) {
            commit("updateOfficerInterviewerId", officer_interviewer_id);
        },

    },
};
