<template>
<form method="POST" name="external_returns_form" enctype="multipart/form-data">
<div class="container" id="externalReturn">
    <Returns v-if="isReturnsLoaded" >
        <div class='col-md-3'/>
        <div class='col-md-9' >

            <ReturnSheet v-if="selected_returns_tab_id===0 && returns.format==='sheet'"></ReturnSheet>
            <ReturnQuestion v-if="selected_returns_tab_id===0 && returns.format==='question'"></ReturnQuestion>
            <ReturnData v-if="selected_returns_tab_id===0 && returns.format==='data'"></ReturnData>
            <ReturnSubmit v-if="selected_returns_tab_id===1 && returns.lodgement_date!=null"></ReturnSubmit>

            <!-- End template for Return Tab -->

            <div class="row" style="margin-bottom:50px;" v-show="showButtons" >
                <div class="navbar navbar-fixed-bottom" style="background-color: #f5f5f5 ">
                    <div class="navbar-inner">
                        <div class="container">
                            <p class="pull-right" style="margin-top:5px;">
                                <strong style="font-size: 18px;" v-if="isPayable">Return submission fee: {{returns_estimate_fee | toCurrency}}</strong><br>

                                  <button v-if="spinner_exit" style="width:150px;" disabled class="btn btn-primary btn-md"><i class="fa fa-spin fa-spinner"></i>&nbsp;Saving</button>
                                  <button v-else-if="!spinner_exit && disable_exit" style="width:150px;" disabled class="btn btn-primary btn-md" name="save_exit">Save and Exit</button>
                                  <button v-else style="width:150px;" class="btn btn-primary btn-md" @click.prevent="save(false)" name="save_exit">Save and Exit</button>

                                  <button v-if="spinner_continue" style="width:150px;"  disabled class="btn btn-primary btn-md"><i class="fa fa-spin fa-spinner"></i>&nbsp;Saving</button>
                                  <button v-else-if="!spinner_continue && disable_continue" disabled style="width:150px;" class="btn btn-primary btn-md" name="save_continue">Save and Continue</button>
                                  <button v-else style="width:150px;" class="btn btn-primary btn-md" @click.prevent="save(true)" name="save_continue">Save and Continue</button>

                                  <button v-if="spinner_submit" style="width:150px;" disabled class="btn btn-primary btn-md"><i class="fa fa-spin fa-spinner"></i>&nbsp;Submitting</button>
                                  <button v-if="!spinner_submit && !isPayable && isSubmittable && !disable_submit" style="width:150px;" class="btn btn-primary btn-md" @click.prevent="save_and_submit()" name="submit">Submit</button>
                                  <button v-else-if="!spinner_submit && disable_submit && !isPayable && isSubmittable" disabled style="width:150px;" class="btn btn-primary btn-md" name="submit">Submit</button>
                                  <button v-else-if="!spinner_submit && !disable_submit && isPayable && isSubmittable" style="width:150px;" class="btn btn-primary btn-md" @click.prevent="submit_and_checkout()" name="submit">Pay and Submit</button>
                                  <button v-else-if="isPayable && isSubmittable && disable_submit" disabled style="width:150px;" class="btn btn-primary btn-md" name="submit">Pay and Submit</button>                           

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
import Vue from 'vue'
import Returns from '../../returns_form.vue'
import ReturnSheet from './enter_return_sheet.vue'
import ReturnQuestion from './enter_return_question.vue'
import ReturnData from './enter_return.vue'
import ReturnSubmit from './return_submit.vue'
import { mapActions, mapGetters } from 'vuex'
import CommsLogs from '@common-components/comms_logs.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
  name: 'externalReturn',
  data() {
    return {
      pdBody: 'pdBody' + self._uid,
      estimated_fee: 0,
      spinner_exit: false,
      spinner_submit: false,
      spinner_continue: false,
      disable_submit: false,
      disable_exit: false,
      disable_continue: false,
      panelClickersInitialised : false,
    }
  },
  components: {
    Returns,
    ReturnSheet,
    ReturnQuestion,
    ReturnData,
    ReturnSubmit,
  },
  computed: {
    ...mapGetters([
        'isReturnsLoaded',
        'returns',
        'species_list',
        'species_cache',
        'species_transfer',
        'selected_returns_tab_id',
        'returns_estimate_fee',
    ]),
    isSubmittable() {
      let submittable = ['Due','Overdue'];
      let can_submit = submittable.indexOf(this.returns.processing_status) > -1

      return can_submit && this.returns.format !== 'sheet' && !this.isPayable
    },
    isPayable() {
      this.setReturnsEstimateFee()
      return this.returns_estimate_fee > 0
    },
    requiresCheckout: function() {
      return this.returns.return_fee > 0 && [
        'draft', 'awaiting_payment'
      ]
    },
    showButtons: function() {
      return this.selected_returns_tab_id===0 && this.returns.is_draft
    },
  },
  methods: {
    ...mapActions({
      load: 'loadReturns',
    }),
    ...mapActions([
        'setReturns',
        'setReturnsExternal',
        'setReturnsEstimateFee',
    ]),
    get_table_data: async function() {
      const self = this;
      self.is_saving = true
      self.form=document.forms.external_returns_form;
      var data = new FormData(self.form);
      // cache only used in Returns sheets
      for (const speciesID in self.species_cache) { // Running Sheet Cache
        let speciesJSON = []
        for (let i=0;i<self.species_cache[speciesID].length;i++){
          // speciesJSON[i] = JSON.stringify(self.species_cache[speciesID][i])
          speciesJSON[i] = self.species_cache[speciesID][i]
        }
        data.append(speciesID, JSON.stringify(speciesJSON))
      };
      var speciesJSON = []
      let cnt = 0;
      for (const speciesID in self.species_transfer) { // Running Sheet Transfers
        Object.keys(self.species_transfer[speciesID]).forEach(function(key) {
          speciesJSON[cnt] = JSON.stringify(self.species_transfer[speciesID][key])
          cnt++;
        });
        data.append('transfer', speciesJSON);
      }
      return data;
    },
    save: async function(andContinue) {
      const self = this;
      self.is_saving = true
      self.disable_submit = true;
      self.disable_exit = true;
      self.disable_continue = true;
      self.spinner_exit = !andContinue;
      self.spinner_continue = andContinue;
      self.form=document.forms.external_returns_form;
      var data = new FormData(self.form);
      // cache only used in Returns sheets
      for (const speciesID in self.species_cache) { // Running Sheet Cache
        let speciesJSON = []
        for (let i=0;i<self.species_cache[speciesID].length;i++){
          // speciesJSON[i] = JSON.stringify(self.species_cache[speciesID][i])
          speciesJSON[i] = self.species_cache[speciesID][i]
        }
        data.append(speciesID, JSON.stringify(speciesJSON))
      };
      var speciesJSON = []
      let cnt = 0;
      for (const speciesID in self.species_transfer) { // Running Sheet Transfers
        Object.keys(self.species_transfer[speciesID]).forEach(function(key) {
          speciesJSON[cnt] = JSON.stringify(self.species_transfer[speciesID][key])
          cnt++;
        });
        data.append('transfer', speciesJSON)
      }
      await self.$http.post(helpers.add_endpoint_json(api_endpoints.returns,self.returns.id+'/save'),data,{
                      emulateJSON:true,
                    }).then((response)=>{
                      let species_id = self.returns.sheet_species;
                      self.setReturns(response.body);
                      self.returns.sheet_species = species_id;
                      self.returns.species = species_id;
                      self.is_saving = false
                      self.disable_submit = false;
                      self.disable_exit = false;
                      self.disable_continue = false;
                      self.spinner_exit = false;
                      self.spinner_continue = false;
                      if (andContinue) { 

                        swal( 'Save', 
                              'Return Details Saved', 
                              'success'
                        )

                      } else { // route back to main dashboard

                        this.$router.push({name:"external-applications-dash",});

                      }
                    },(error)=>{
                      self.is_saving = false
                      self.disable_submit = false;
                      self.disable_exit = false;
                      self.disable_continue = false;
                      self.spinner_exit = false;
                      self.spinner_continue = false;
                      console.log(error);
                      swal('Error',
                           'There was an error saving your return details.<br/>' + error.body,
                           'error'
                      )
                    });
    },
    save_and_submit: async function(e) {
      const self = this;
      // self.is_submitting = true;
      self.disable_continue = true;
      self.disable_exit = true;
      self.disable_submit = true;
      self.spinner_submit = true;
      var data = await self.get_table_data()

      await self.$http.post(helpers.add_endpoint_json(api_endpoints.returns,self.returns.id+'/save_and_submit'),data,{
                      emulateJSON:true,
                    }).then((response)=>{
                      // self.is_submitting = false;
                      self.disable_submit = false;
                      self.disable_exit = false;
                      self.disable_continue = false;
                      self.spinner_submit = false;
                      this.$router.push({name:"external-applications-dash"});

                    },(error)=>{
                      // self.is_submitting = false
                      self.disable_exit = false;
                      self.disable_submit = false;
                      self.disable_continue = false;
                      self.spinner_submit = false;
                      console.log(error);
                      swal('Error',
                           'There was an error saving and submitting your return details.<br/>' + error.body,
                           'error'
                      )
                    });
    },
    submit: async function(e) {
      const self = this;
      // self.is_submitting = true
      self.disable_continue = true;
      self.disable_exit = true;
      self.disable_submit = true;
      self.spinner_exit = true;
      self.spinner_submit = true;
      self.form=document.forms.external_returns_form;
      self.$http.post(helpers.add_endpoint_json(api_endpoints.returns,self.returns.id+'/submit'),{
                      emulateJSON:true,
                    }).then((response)=>{
                       let species_id = self.returns.sheet_species;
                       self.setReturns(response.body);
                       self.returns.sheet_species = species_id;
                       self.disable_continue = false;
                       self.disable_exit = false;
                       self.disable_submit = false;
                       self.spinner_exit = false;
                       self.spinner_submit = false;
                       this.$router.push({name:"external-applications-dash"});
                    },(error)=>{
                       self.disable_continue = false;
                       self.disable_exit = false;
                       self.disable_submit = false;
                       self.spinner_exit = false;
                       self.spinner_submit = false;
                       console.log(error);
                       swal('Error',
                            'There was an error submitting your return details.<br/>' + error.body,
                            'error'
                       )
                    });

    },
    submit_and_checkout: async function(e) {
      const self = this;
      self.disable_continue = true;
      self.disable_exit = true;
      self.disable_submit = true;
      self.spinner_exit = true;
      self.spinner_submit = true;
      self.form=document.forms.external_returns_form;
      await self.$http.post(helpers.add_endpoint_json(api_endpoints.returns,self.returns.id+'/submit_and_checkout'),{
                      emulateJSON:true,
                    }).then((response)=>{
                       self.disable_continue = false;
                       self.disable_exit = false;
                       self.disable_submit = false;
                       self.spinner_exit = false;
                       self.spinner_submit = false;

                       window.location.href = "/ledger/checkout/checkout/payment-details/";
                       //let species_id = self.returns.sheet_species;
                       //self.setReturns(response.body);
                       //self.returns.sheet_species = species_id;
                    },(error)=>{
                       self.disable_continue = false;
                       self.disable_exit = false;
                       self.disable_submit = false;
                       self.spinner_exit = false;
                       self.spinner_submit = false;
                       console.log(error);
                       swal('Error',
                            'There was an error submitting your return details.<br/>' + error.body,
                            'error'
                       )
                    
                    });

    },
  },
  beforeRouteEnter: function(to, from, next) {
     next(vm => {
       vm.load({ url: `/api/returns/${to.params.return_id}.json` });
       vm.setReturnsExternal({'external': true});
     });  // User and Return Store loaded.
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
    console.log('mounted')
      // 
  },
}
</script>
