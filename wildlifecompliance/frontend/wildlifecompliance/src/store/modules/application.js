import Vue from 'vue';
import {
    UPDATE_APPLICATION,
    UPDATE_ORIGINAL_APPLICATION,
    UPDATE_ORG_APPLICANT,
    UPDATE_PROXY_APPLICANT,
    UPDATE_APPLICATION_CHECK_STATUS_ID,
    UPDATE_APPLICATION_CHECK_STATUS_CHARACTER,
    UPDATE_APPLICATION_CHECK_STATUS_RETURN,
    UPDATE_APPLICATION_FEE_STATUS,
    UPDATE_APPLICATION_ASSESS_STATUS,
} from '@/store/mutation-types';


export const applicationStore = {
    state: {
        original_application: {},
        application: {
            "schema": [],
            "licence_type_data": {
                "activity": []
            }
        },
        id_check_status: null,
        character_check_status: null,
        return_check_status: null,
    },
    getters: {
        application: state => state.application,
        original_application: state => state.original_application,
        amendment_requests: state => state.application.amendment_requests,
        application_id: state => state.application.id,
        licence_type_data: state => state.application.licence_type_data,
        org_address: state => state.application.org_applicant != null && state.application.org_applicant.address != null ? state.application.org_applicant.address : {},
        proxy_address: state => state.application.proxy_applicant != null && state.application.proxy_applicant.address != null ? state.application.proxy_applicant.address : {},
        application_readonly: state => state.application.readonly,
        id_check_status: state => state.id_check_status,
        character_check_status: state => state.character_check_status,
        return_check_status: state => state.return_check_status,
        applicant_type: state => {
            if (state.application.org_applicant){
                return 'org';
            } else if (state.application.proxy_applicant){
                return 'proxy';
            }
            return 'submitter';
        },
        checkActivityStatus: (state, getters, rootState, rootGetters) => (status_list, status_count=1, required_role=null) => {
            if(status_list.constructor !== Array) {
                status_list = [status_list];
            }
            const activities_list = getters.licence_type_data.activity;
            return activities_list.filter(activity =>
                status_list.includes(activity.processing_status.id)
                && (required_role === null || rootGetters.hasRole(required_role, activity.id))
            ).length >= status_count;
        },
        isFinalised: (state, getters) => {
            return getters.checkActivityStatus([
                'declined',
                'accepted'
            ], getters.licence_type_data.activity.length);
        },
        isPartiallyFinalised: (state, getters) => {
            const final_statuses = [
                'declined',
                'accepted'
            ];
            const activity_count = getters.licence_type_data.activity.length;
            return getters.checkActivityStatus(final_statuses) && !getters.checkActivityStatus(final_statuses, activity_count);
        },
        isApplicationLoaded: state => Object.keys(state.application).length && state.application.licence_type_data.activity.length,
        isApplicationActivityVisible: (state, getters, rootState, rootGetters) =>
            ({activity_id,
              exclude_statuses,
              exclude_processing_statuses,
              for_user_role,
              only_processing_statuses,
            }) => {
            if(!state.application.activities) {
                return 0;
            }
            return getters.filterActivityList({
                activity_list: state.application.activities,
                activity_id: activity_id,
                only_processing_statuses: only_processing_statuses,
                exclude_statuses: exclude_statuses,
                exclude_processing_statuses: exclude_processing_statuses,
                for_user_role: for_user_role,
                licence_activity_id_key: 'licence_activity'
            }).length;
        },
        licenceActivities: (state, getters) => (activity_status, for_user_role) => {
            return getters.filterActivityList({
                activity_list: getters.licence_type_data.activity,
                only_processing_statuses: activity_status,
                for_user_role: for_user_role,
            });
        },
        filterActivityList: (state, getters, rootState, rootGetters) =>
            ({activity_list,
              activity_id,
              exclude_statuses,
              only_processing_statuses,
              exclude_processing_statuses,
              for_user_role,
              licence_activity_id_key='licence_activity'
            }) => {

            if(!activity_list.length) {
                return [];
            }
            return activity_list.filter(
                activity =>
                (!activity_id || activity[licence_activity_id_key] == activity_id) &&
                (!exclude_statuses ||
                    !(exclude_statuses.constructor === Array ? exclude_statuses : [exclude_statuses]
                        ).includes(activity.decision_action)) &&
                (!only_processing_statuses ||
                    (only_processing_statuses.constructor === Array ? only_processing_statuses : [only_processing_statuses]
                        ).includes(activity.processing_status.id ? activity.processing_status.id : activity.processing_status)) &&
                (!exclude_processing_statuses ||
                    !(exclude_processing_statuses.constructor === Array ? exclude_processing_statuses : [exclude_processing_statuses]
                        ).includes(activity.processing_status.id ? activity.processing_status.id : activity.processing_status)) &&
                (!for_user_role || rootGetters.hasRole(for_user_role, activity[licence_activity_id_key]))
            );
        },
        sendToAssessorActivities: (state, getters) => {
            // Application status which permits sending assessments for licensing Officer.
            return getters.licenceActivities(['with_officer', 'with_officer_conditions', 'with_assessor'], 'licensing_officer');
        },
    },
    mutations: {
        [UPDATE_APPLICATION] (state, application) {
            Vue.set(state, 'application', {...application});
        },
        [UPDATE_ORIGINAL_APPLICATION] (state, application) {
            Vue.set(state, 'original_application', {...application});
        },
        [UPDATE_ORG_APPLICANT] (state, { key, value }) {
            if(state.application.org_applicant == null) {
                Vue.set(state.application, "org_applicant", {});
            }
            Vue.set(state.application.org_applicant, key, value);
        },
        [UPDATE_PROXY_APPLICANT] (state, { key, value }) {
            if(state.application.proxy_applicant == null) {
                Vue.set(state.application, "proxy_applicant", {});
            }
            Vue.set(state.application.proxy_applicant, key, value);
        },
        [UPDATE_APPLICATION_CHECK_STATUS_ID] (state, id_status) {
            Vue.set(state, 'id_check_status', id_status);
        },
        [UPDATE_APPLICATION_CHECK_STATUS_CHARACTER] (state, character_status) {
            Vue.set(state, 'character_check_status', character_status);
        },
        [UPDATE_APPLICATION_CHECK_STATUS_RETURN] (state, return_status) {
            Vue.set(state, 'return_check_status', return_status);
        },
        [UPDATE_APPLICATION_FEE_STATUS] (state, fee_status) {
            Vue.set(state.application, 'update_fee', fee_status);
        },
        [UPDATE_APPLICATION_ASSESS_STATUS] (state, assess_status) {
            Vue.set(state.application, 'assess', assess_status);
        },
    },
    actions: {
        refreshAddresses({ commit, state, getters }) {
            if (getters.applicant_type === 'org') {
                commit(UPDATE_ORG_APPLICANT, {key: 'address', value: state.org_address});
            };
            if (getters.applicant_type === 'proxy') {
                commit(UPDATE_PROXY_APPLICANT,  {key: 'address', value: state.proxy_address});
            };
        }, 
        loadApplication({ dispatch, state, commit }, { url }) {
            return new Promise((resolve, reject) => {
                Vue.http.get(url).then(res => {
                    dispatch('setOriginalApplication', res.body);
                    dispatch('setApplication', res.body);
                    dispatch('setApplication', {
                       ...state.application,
                       application_fee: res.body.adjusted_paid_amount.application_fee,
                       licence_fee: res.body.adjusted_paid_amount.licence_fee,
                       update_fee: false,
                       assess: false,
                    });
                    for(let form_data_record of res.body.data) {
                        dispatch('setFormValue', {
                            key: form_data_record.field_name,
                            value: {
                                "value": form_data_record.value,
                                "officer_comment": form_data_record.officer_comment,
                                "assessor_comment": form_data_record.assessor_comment,
                                "deficiency_value": form_data_record.deficiency,
                                "schema_name": form_data_record.schema_name,
                                "component_type": form_data_record.component_type,
                                "instance_name": form_data_record.instance_name,
                                "licence_activity_id": form_data_record.licence_activity_id,
                                "licence_purpose_id": form_data_record.licence_purpose_id,
                                "component_attribute": form_data_record.component_attribute,
                            }
                        });
                    }
                    dispatch('setIdCheckStatus', res.body.id_check_status.id);
                    dispatch('setCharacterCheckStatus', res.body.character_check_status.id);
                    dispatch('setReturnCheckStatus', res.body.return_check_status.id);
                    resolve();
                },
                err => {
                    console.log(err);
                    reject();
                });
            })
        },
        revertApplication({ dispatch, commit, state }) {
            commit(UPDATE_APPLICATION, state.original_application);
            //dispatch('refreshAddresses'); 
        },
        setOriginalApplication({ commit }, application) {
            commit(UPDATE_ORIGINAL_APPLICATION, application);
        },
        setApplication({ dispatch, commit }, application) {
            commit(UPDATE_APPLICATION, application);
            //dispatch('refreshAddresses'); this would cause the organisation/proxy address to be removed from json response body, so has been commented out for now
        },
        refreshApplicationFees({ dispatch, state, getters, rootGetters }) {
            Vue.http.post('/api/application/estimate_price/', {
                    'application_id': getters.application_id,
                    'field_data': rootGetters.renderer_form_data,
            }).then(res => {
                dispatch('setApplication', {
                    ...state.application,
                    application_fee: res.body.fees.application,
                    licence_fee: res.body.fees.licence,
                    update_fee: true,
                    assess: true,
                });
            }, err => {
                console.log(err);
            });
        },
        setIdCheckStatus({ commit }, id_status) {
            commit(UPDATE_APPLICATION_CHECK_STATUS_ID, id_status);
        },
        setCharacterCheckStatus({ commit }, character_status) {
            commit(UPDATE_APPLICATION_CHECK_STATUS_CHARACTER, character_status);
        },
        setReturnCheckStatus({ commit }, return_status) {
            commit(UPDATE_APPLICATION_CHECK_STATUS_RETURN, return_status);
        },
        setAssessStatus({ commit }, assess_status) {
            commit(UPDATE_APPLICATION_ASSESS_STATUS, assess_status);
        },
        resetUpdateFeeStatus({ commit }) {
            commit(UPDATE_APPLICATION_FEE_STATUS, false);
        },
        setLicenceTypeData({ dispatch, state, getters, rootGetters }, activity_data) {
            return new Promise((resolve, reject) => {
                Vue.http.post('/api/application/' + getters.application_id + '/update_licence_type_data/', {
                        'application_id': getters.application_id,
                        'licence_activity_id': activity_data.licence_activity_id,
                        'licence_activity_workflow': activity_data.workflow,
                }).then(res => {
                    dispatch('setApplication', res.body);
                    dispatch('setApplication', {
                        ...state.application,
                        application_fee: res.body.adjusted_paid_amount.application_fee,
                        licence_fee: res.body.adjusted_paid_amount.licence_fee,
                        update_fee: false,
                        assess: false,
                    });
                    resolve();
                }, err => {
                    console.log(err);
                    reject();
                });
            });
        },
    }
}
