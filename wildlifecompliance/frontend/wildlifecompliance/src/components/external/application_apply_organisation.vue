<template lang="html" >
    <div class="container" >
        <div class="row">
            <div class="col-sm-12">
                <FormSection
                :form-collapse="false"
                label="Apply on behalf of"
                index="apply"
                >
                    <div class="panel panel-default">
                        <form class="form-horizontal" name="personal_form" method="post">
                            <div class="col-sm-12">
                                    <!-- <p><strong>Note: If you are applying for a Taking licence, it cannot be applied for on behalf of an organisation.</strong></p> -->
                                    <div class="radio">
                                        <label>
                                        <input type="radio"  name="behalf_of_org" v-model="org_applicant" value=""> On behalf of yourself
                                        </label>
                                    </div>
                                    <div v-for="org in current_user.wildlifecompliance_organisations" class="radio">
                                        <label v-if ="!org.is_consultant">
                                          <input type="radio"  name="behalf_of_org" v-model="org_applicant"  :value="org.id"> On behalf of {{org.name}}
                                        </label>
                                        <label v-if ="org.is_consultant">
                                          <input  type="radio"  name="behalf_of_org" v-model="org_applicant"  :value="org.id" > On behalf of {{org.name}} (as a Consultant)
                                        </label>
                                    </div>
                                    <div v-if="current_user.is_internal" class="radio">
                                        <label>
                                        <input type="radio" name="behalf_of_org" value="external" v-model="org_applicant"> On behalf of an External User/Organisation
                                        </label>
                                    </div>
                                    <div v-show="org_applicant == 'external'">
                                        <div class="col-sm-6">
                                            <select 
                                                id="person_lookup"  
                                                name="person_lookup"  
                                                ref="person_lookup" 
                                                class="form-control" 
                                            />
                                        </div>
                                    </div>
                            </div>
                           
                            <div class="col-sm-12">
                                <button :disabled="org_applicant === null" @click.prevent="submit()" class="btn btn-primary float-end">Continue</button>
                            </div>
                        </form>
                    </div>
                </FormSection>
            </div>
        </div>
    </div>
</template>
<script>
import { v4 as uuid } from 'uuid';
import {
  api_endpoints,
  helpers, fetch_util
}
from '@/utils/hooks'
import { mapActions, mapGetters } from 'vuex'
import utils from './utils'
import $ from 'jquery'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
  data: function() {
    let vm = this;
    return {
        "application": null,
        agent: {},
        org_applicant: "",
        organisations:null,
        current_user: {
            wildlifecompliance_organisations: []
        },
        "loading": [],
        form: null,
        pBody: 'pBody' + uuid(),

        personOrgEntity: {},
    }
  },
  components: {
    FormSection
  },
  computed: {
    isLoading: function() {
      return this.loading.length > 0
    },
    org: function() {
        let vm = this;
        if (vm.org_applicant && !isNaN(vm.org_applicant)) {
            return vm.current_user.wildlifecompliance_organisations.find(org => parseInt(org.id) === parseInt(vm.org_applicant)).name;
        }
        return '';
    }
  },
  methods: {
    ...mapActions([
        'setApplyOrgId',
        'setApplyUserId',
        'setApplicationWorkflowState',
    ]),
    fetchOrgId: function (id) {
        return fetch_util.fetchUrl(
            helpers.add_endpoint_json(
                api_endpoints.organisation_requests + id + '/',
                'get_approved_org_id'
            )
        )
        .then(response => response.org_id)
        .catch(error => {
            console.log(error);
            throw error;
        });
    },
    submit: async function() {
        let vm = this;
        
        if (vm.personOrgEntity) {
            if (vm.personOrgEntity.entity_type == "org") {
                //get org id from org request id 
                const org_id = await vm.fetchOrgId(vm.personOrgEntity.id);
                vm.setApplyOrgId({id: org_id});
                vm.setApplyUserId({id: ''});
            } else if (vm.personOrgEntity.entity_type == "user") {
                vm.setApplyUserId({id: vm.personOrgEntity.id});
                vm.setApplyOrgId({id: ''});
            }
        }
        else {
            vm.setApplyOrgId({id: vm.org_applicant});
            vm.setApplyUserId({id: ''});
        }
        vm.setApplicationWorkflowState({bool: true});
        vm.$router.push({
            name:"apply_application",
        });
    },
    
    fetchOrgContact:function (){
        let vm =this;
        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.organisation_requests,'get_pending_requests'))
        request.then((response)=>{
            vm.orgRequest_pending = response;
            vm.loading.splice('fetching pending organisation requests',1);
        }).catch((error) => {
            console.log(error)
        });
    },
    initialisePersonLookup: function(){
        let vm = this;
        $(vm.$refs.person_lookup).select2({
            minimumInputLength: 2,
            "theme": "bootstrap-5",
            allowClear: true,
            placeholder:"Select Person",
            ajax: {
                url: api_endpoints.person_org_lookup,
                dataType: 'json',
                data: function(params) {
                    var query = {
                        term: params.term,
                        option: "starts_with",
                        type: 'public',
                    }
                    return query;
                },
            },
        }).
        on("select2:select", function (e) {
            var selected = $(e.currentTarget);
            vm.personOrgEntity = Object.assign({}, e.params.data);
            console.log(vm.personOrgEntity)
        }).
        on("select2:unselect",function (e) {
            var selected = $(e.currentTarget);
            vm.personOrgEntity = {};
        }).
        on("select2:open",function (e) {
            const searchField = $('[aria-controls="select2-person_lookup-results"]')
            searchField[0].focus();
        });
    },
  },
  mounted: function() {
    let vm = this;
    vm.form = document.forms.new_application;
    this.initialisePersonLookup();
  },
  beforeRouteEnter:function(to,from,next){
        let initialisers = [
            utils.fetchCurrentUser(),
        ]
        Promise.all(initialisers).then(data => {
            next(vm => {
                vm.current_user = data[0];
            });
        });
    },
}
</script>

<style lang="css">
</style>
