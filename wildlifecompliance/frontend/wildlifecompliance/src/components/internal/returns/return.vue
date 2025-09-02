<template>
<form method="POST" name="internal_returns_form" enctype="multipart/form-data">
<div class="container" id="internalReturn">
    <Returns v-if="isReturnsLoaded">
        <div class="col-md-8">
        <FormSection
            :form-collapse="false"
            label="Condition Details"
        >                
            <div class="panel panel-default">
                <div class="col-sm-8">
                    <form class="form-horizontal" name="return_form">
                        <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Licence Activity</label>
                            <div class="col-sm-6" v-if='returns.condition'>
                                {{returns.condition.licence_activity.name}}
                            </div>                         
                            <div class="col-sm-6" v-else> &nbsp;</div>                        
                        </div>
                        <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Condition</label>
                            <div class="col-sm-6" v-if='returns.condition'>
                                <textarea disabled class="form-control" name="details" placeholder="" v-model="returns.condition.condition"></textarea>
                            </div>
                            <div class="col-sm-6" v-else> &nbsp;</div>
                        </div>
                        <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Due Date</label>
                            <div class="col-sm-6" v-if='returns.condition'>
                                {{returns.condition.due_date}}
                            </div>
                            <div class="col-sm-6" v-else> &nbsp;</div>
                        </div>
                    </form>
                </div>
            </div>
        </FormSection>

        <ReturnSheet v-if="returns.format==='sheet'"></ReturnSheet>
        <ReturnQuestion v-if="returns.format==='question'"></ReturnQuestion>
        <ReturnData v-if="returns.format==='data'"></ReturnData>

        <!-- End template for Return Tab -->

        <div v-show="showSaveAndContinueButton" class="row" style="margin-bottom:50px;">
            <div class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
                <div class="navbar-inner">
                    <div class="container">
                        <p class="pull-right" style="margin-top:5px;">
                            <button v-if="spinner_exit" style="width:150px;" disabled class="btn btn-primary btn-md"><i class="fa fa-spin fa-spinner"></i>&nbsp;Saving</button>
                            <button v-else-if="!spinner_exit && disable_exit" style="width:150px;" disabled class="btn btn-primary btn-md" name="save_exit">Save and Exit</button>
                            <button v-else style="width:150px;" class="btn btn-primary btn-md" @click.prevent="saveandcontinue(false)" name="save_exit">Save and Exit</button>

                            <button v-if="spinner_continue" style="width:150px;"  disabled class="btn btn-primary btn-md"><i class="fa fa-spin fa-spinner"></i>&nbsp;Saving</button>
                            <button v-else-if="!spinner_continue && disable_continue" disabled style="width:150px;" class="btn btn-primary btn-md" name="save_continue">Save and Continue</button>
                            <button v-else style="width:150px;" class="btn btn-primary btn-md" @click.prevent="saveandcontinue(true)" name="save_continue">Save and Continue</button>
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <div v-show="showSaveButton" class="row" style="margin-bottom:50px;">
            <div class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
                <div class="navbar-inner">
                    <div class="container">
                        <p class="pull-right" style="margin-top:5px;">
                            <button v-if="showSpinner" type="button" class="btn btn-primary" ><i class="fa fa-spinner fa-spin"/>Saving</button>                                                    
                            <button v-else style="width:150px;" class="btn btn-primary btn-md" @click.prevent="save()" name="save_exit">Save Changes</button>
                        </p>
                    </div>
                </div>
            </div>
        </div>

        </div>
    </Returns>
</div>
</form>
</template>

<script>
import { v4 as uuid } from 'uuid';
import Vue from 'vue'
import { mapActions, mapGetters } from 'vuex'
import Returns from '../../returns_form.vue'
import ReturnQuestion from '../../external/returns/enter_return_question.vue'
import ReturnSheet from '../../external/returns/enter_return_sheet.vue'
import ReturnData from '../../external/returns/enter_return.vue'
import CommsLogs from '@common-components/comms_logs.vue'
import {
  api_endpoints,
  helpers,
  fetch_util
}
from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
  name: 'internal-returns',
  data() {
    let vm = this;
    return {
        pdBody: 'pdBody' + uuid(),
        panelClickersInitialised: false,
        loading: [],
        spinner: false,
        spinner_exit: false,
        spinner_continue: false,
        disable_exit: false,
        disable_continue: false,
    
        DATE_TIME_FORMAT: 'DD/MM/YYYY HH:mm:ss',
        members: [],

        // Filters
        logs_url: helpers.add_endpoint_json(api_endpoints.returns,vm.$route.params.return_id+'/action_log'),
        comms_url: helpers.add_endpoint_json(api_endpoints.returns,vm.$route.params.return_id+'/comms_log'),
        comms_add_url: helpers.add_endpoint_json(api_endpoints.returns,vm.$route.params.return_id+'/add_comms_log'),

    }
  },
  components: {
    FormSection,
    Returns,
    CommsLogs,
    ReturnQuestion,
    ReturnSheet,
    ReturnData,
  },
  computed: {
     ...mapGetters([
        'isReturnsLoaded',
        'returns',
        'is_external',
        'species_cache',
    ]),
    showSpinner: function() {
        return this.spinner
    },
    showSaveButton: function() {
        return !this.returns.is_draft && this.returns.can_be_processed && this.returns.user_in_officers;
    },
    showSaveAndContinueButton: function() {
        return this.returns.is_draft && this.returns.user_in_officers;
    },
  },
  methods: {
    ...mapActions({
      load: 'loadReturns',
    }),
    ...mapActions([
        'setReturns',
    ]),
    save: function(props = { showNotification: true }) {
        this.spinner = true;
        const { showNotification } = props;
        this.form=document.forms.internal_returns_form;
        var data = new FormData(this.form);

        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.returns,this.returns.id+'/officer_comments'),{method:'POST', body:JSON.stringify(data)},{
                      emulateJSON:true,

        })
        request.then((response)=>{
            this.spinner = false;
            let species_id = this.returns.sheet_species;
            this.setReturns(response);
            this.returns.sheet_species = species_id;

            swal.fire( 'Save', 
                'Return Details Saved', 
                'success' )
        
        },(error)=>{
            this.spinner = false
            console.log(error);
            swal.fire('Error',
                'There was an error saving your return details.<br/>' + error.body,
                'error'
            )
        });
    },
    saveandcontinue: async function(andContinue) {
      this.is_saving = true
      this.disable_submit = true;
      this.disable_exit = true;
      this.disable_continue = true;
      this.spinner_exit = !andContinue;
      this.spinner_continue = andContinue;
      this.form=document.forms.internal_returns_form;
      var data = new FormData(this.form);
      // cache only used in Returns sheets
      for (const speciesID in this.species_cache) { // Running Sheet Cache
        let speciesJSON = []
        for (let i=0;i<this.species_cache[speciesID].length;i++){
          speciesJSON[i] = this.species_cache[speciesID][i]
        }
        data.append(speciesID, JSON.stringify(speciesJSON))
      };
      var speciesJSON = []
      let cnt = 0;
      for (const speciesID in this.species_transfer) { // Running Sheet Transfers
        Object.keys(this.species_transfer[speciesID]).forEach(function(key) {
          speciesJSON[cnt] = JSON.stringify(this.species_transfer[speciesID][key])
          cnt++;
        });
        data.append('transfer', speciesJSON)
      }
        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.returns,this.returns.id+'/save'),{method:'POST', body:data},{
            emulateJSON:true,
        })
        request.then((response)=>{
            let species_id = this.returns.sheet_species;
            this.setReturns(response);
            this.returns.sheet_species = species_id;
            this.returns.species = species_id;
            this.is_saving = false
            this.disable_submit = false;
            this.disable_exit = false;
            this.disable_continue = false;
            this.spinner_exit = false;
            this.spinner_continue = false;
        if (andContinue) { 

            swal.fire( 'Save', 
                    'Return Details Saved', 
                    'success'
            )

            } else { // route back to main dashboard

            this.$router.push({name:"internal-returns-dash",});

            }
        },(error)=>{
            this.is_saving = false
            this.disable_submit = false;
            this.disable_exit = false;
            this.disable_continue = false;
            this.spinner_exit = false;
            this.spinner_continue = false;
            console.log(error);
            swal.fire('Error',
                'There was an error saving your return details.<br/>' + error.body,
                'error'
            )
        });
    },
  },
  beforeRouteEnter: function(to, from, next){
     next(vm => {
       vm.load({ url: `/api/returns/${to.params.return_id}.json` });
     });  // Return Store loaded.
  },
  updated: function(){
      const self = this;
      if (!self.panelClickersInitialised){
          $('.panelClicker[data-toggle="collapse"]').on('click', function () {
              var chev = $(this).children()[0];
              window.setTimeout(function () {
                  $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
              },100);
          }); 
          self.panelClickersInitialised = true;
      }
  },
  mounted: function() {
      // 
  },
}

</script>
