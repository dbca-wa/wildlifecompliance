import Vue from 'vue'
import api from './api'
import {api_endpoints, helpers, fetch_util} from '@/utils/hooks' 

export default {
    fetchCurrentUser: function (){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.my_user_details)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilApplication: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.applications,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilCountries: function (){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.countries)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilOrganisations: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.organisations)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilOrganisationPermissions: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.my_organisations,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilLicenceClasses: function(){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.licences_class)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilLicenceAvailablePurposes: function(params){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.licence_available_purposes, {"params": params})
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilOrganisationId: function(org_id) {
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api_endpoints.get_organisation_id(org_id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilOrganisation: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.organisations,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilCurrentActiveLicenceApplication: function(params){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(`${api.applications}active_licence_application`, {"params": params})
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
}
