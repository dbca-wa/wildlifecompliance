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
                            </div>
                           
                            <div class="col-sm-12">
                                <button :disabled="org_applicant === null" @click.prevent="submit()" class="btn btn-primary pull-right">Continue</button>
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
import Vue from 'vue'
import {
  api_endpoints,
  helpers, fetch_util
}
from '@/utils/hooks'
import { mapActions, mapGetters } from 'vuex'
import utils from './utils'
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
        'setApplicationWorkflowState',
    ]),
    submit: function() {
        let vm = this;
        vm.setApplyOrgId({id: vm.org_applicant});
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
  },
   
  mounted: function() {
    let vm = this;
    vm.form = document.forms.new_application;
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
