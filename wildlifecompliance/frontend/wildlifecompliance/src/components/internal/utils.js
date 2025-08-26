import Vue from 'vue'
import api from './api'
import {helpers, fetch_util} from '@/utils/hooks' 

export default {
    fetchApplication: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.applications,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchOrganisations: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.organisations)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchOrganisation: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.organisations,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchOrganisationPermissions: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.my_organisations,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchOrgRequestPending:function (id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_join(api.users,id + '/pending_org_requests'))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchProfile: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.profiles,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchUsers: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.users)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchUser: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.users,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetchOffender: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.offenders,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
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
    fetchCountries: function (){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.countries)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
}
