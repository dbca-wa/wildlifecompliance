import Vue from 'vue'
import api from './api'
import {api_endpoints, helpers, fetch} from '@/utils/hooks' 

export default {
    fetchCurrentUser: function (){
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(api.my_user_details)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchApplication: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(helpers.add_endpoint_json(api.applications,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchCountries: function (){
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(api.countries)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchOrganisations: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(api.organisations)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchOrganisationPermissions: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(helpers.add_endpoint_json(api.my_organisations,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchLicenceClasses: function(){
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(api.licences_class)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchLicenceAvailablePurposes: function(params){
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(api.licence_available_purposes, {"params": params})
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchOrganisationId: function(org_id) {
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(api_endpoints.get_organisation_id(org_id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchOrganisation: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(helpers.add_endpoint_json(api.organisations,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchCurrentActiveLicenceApplication: function(params){
        return new Promise ((resolve,reject) => {
            let request = fetch.fetchUrl(`${api.applications}active_licence_application`, {"params": params})
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
}
