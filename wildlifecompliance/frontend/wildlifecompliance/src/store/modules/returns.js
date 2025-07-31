import Vue from 'vue';
import {
    UPDATE_RETURNS,
    UPDATE_RETURNS_ESTIMATE,
} from '@/store/mutation-types';

import { fetch } from '@/utils/hooks';

export const returnsStore = {
    state: {
        returns: {
            submitter: '',
            processing_status: '',
        },
        returns_estimate_fee: 0,
    },
    getters: {
        return_id: state => state.returns.id,
        returns: state => state.returns,
        isReturnsLoaded: state => Object.keys(state.returns).length && state.returns.table != null,
        returns_estimate_fee: state => state.returns_estimate_fee,
    },
    mutations: {
        [UPDATE_RETURNS] (state, returns) {
            state.returns = {...returns};
        },
        [UPDATE_RETURNS_ESTIMATE] (state, estimate) {
            state.returns_estimate_fee = estimate;
        },
    },
    actions: {
        loadReturns({ dispatch, commit }, { url }) {
            return new Promise((resolve, reject) => {
                let request = fetch.fetchUrl(url)
                request.then(res => {
                    if (res.format !== 'sheet') {    // Return Sheets utilise Non-rendered data.
                        var obj = res.table[0]['data'][0]
                        for(let form_data_record of Object.keys(obj)) {
                            let deficiency_key = form_data_record + '-deficiency-field'    
                            dispatch('setFormValue', {
                                key: form_data_record,
                                value: {
                                    "value" :  obj[form_data_record], 
                                    "deficiency_value": obj[deficiency_key],                               
                                }
                            });

                        }
                    }

                    dispatch('setReturns', res);
                    resolve();
                }).catch((error) => {
                    console.log(error);
                    reject();
                });
            })
        },
        setReturns({ dispatch, commit }, returns) {
            commit(UPDATE_RETURNS, returns);
        },
        setReturnsEstimateFee({ dispatch, getters, commit }) {
            let estimate = 0
            if (getters.returns.has_data){
                let rows = getters.returns.table[0]['data']
                let qty = 0
                if (getters.returns.apply_fee_field) {
    
                    for (let i=0; i<rows.length; i++){
                        qty += parseInt(rows[i][getters.returns.apply_fee_field]['value'])
                    }
                }
                let estimate = qty * getters.returns.base_fee
            }

            estimate = (estimate - getters.returns.total_paid_amount) > 0 ? estimate - getters.returns.total_paid_amount : 0
            commit(UPDATE_RETURNS_ESTIMATE, estimate);
        },
    }
}
