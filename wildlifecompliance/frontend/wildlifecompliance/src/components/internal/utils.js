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
    fetch_utilOrgRequestPending:function (id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_join(api.users,id + '/pending_org_requests'))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilProfile: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.profiles,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilUsers: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.users)
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilUser: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.users,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilOffender: function(id){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api.offenders,id))
            request.then((response) => {
                resolve(response);
            }).catch((error) => {
                reject(error);
            });
        });
    },
    fetch_utilCurrentUser: function (){
        return new Promise ((resolve,reject) => {
            let request = fetch_util.fetchUrl(api.my_user_details)
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
}
