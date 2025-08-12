<template lang="html">
    <div>
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
            <div class="container-fluid">
                <div class="row">
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="first_name">First Name</label>
                        </div>
                        <div class="col-sm-6">
                            <div v-if="offender_person">
                                <input type="text" class="form-control" name="first_name" placeholder="" v-model="offender_person.first_name" v-bind:key="offender_id">
                            </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="last_name">Last Name</label>
                        </div>
                        <div class="col-sm-6">
                            <div v-if="offender_person">
                                <input type="text" class="form-control" name="last_name" placeholder="" v-model="offender_person.last_name" v-bind:key="offender_id">
                            </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="dob">Date of Birth</label>
                        </div>
                        <div class="col-sm-6">
                            <div v-if="offender_person">
                                <div class="input-group date" ref="dobDatePicker">
                                    <input 
                                    name="dob"
                                    type="date" 
                                    class="form-control" 
                                    placeholder="DD/MM/YYYY" 
                                    v-model="offender_person.dob" 
                                    />
                                    <!--<span class="input-group-addon">
                                        <span class="glyphicon glyphicon-calendar"></span>
                                    </span>-->
                                </div>
                            </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="phone_number">Phone Number</label>
                        </div>
                        <div class="col-sm-6">
                            <div v-if="offender_person">
                                <input type="text" class="form-control" name="phone_number" placeholder="" v-model="offender_person.phone_number" v-bind:key="offender_id">
                            </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="mobile_number">Mobile Number</label>
                        </div>
                        <div class="col-sm-6">
                            <div v-if="offender_person">
                                <input type="text" class="form-control" name="mobile_number" placeholder="" v-model="offender_person.mobile_number" v-bind:key="offender_id">
                            </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="address_street">Street</label>
                        </div>
                        <div class="col-sm-6">
                            <div v-if="offender_person">
                                <input type="text" class="form-control" name="address_street" placeholder="" v-model="offender_person.address_street" v-bind:key="offender_id">
                            </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="address_locality">Locality</label>
                        </div>
                        <div class="col-sm-6">
                            <div v-if="offender_person">
                                <input type="text" class="form-control" name="address_locality" placeholder="" v-model="offender_person.address_locality" v-bind:key="offender_id">
                            </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="address_state">State</label>
                        </div>
                        <div class="col-sm-3">
                            <div v-if="offender_person">
                                <input type="text" class="form-control" name="address_state" placeholder="" v-model="offender_person.address_state" v-bind:key="offender_id">
                            </div>
                        </div>
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="address_postcode">Postcode</label>
                        </div>
                        <div class="col-sm-3">
                            <div v-if="offender_person">
                                <input type="text" class="form-control" name="address_postcode" placeholder="" v-model="offender_person.address_postcode" v-bind:key="offender_id">
                            </div>
                        </div>
                      </div>
                    </div>
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="offence-identifier">Country</label>
                        </div>
                        <div class="col-sm-6">
                            <div v-if="offender_person">
                                <select class="form-control" name="country" placeholder="" v-model="offender_person.address_country">
                                    <option v-for="c in countries" :value="c.code">{{ c.name }}</option>
                                </select>                            
                            </div>
                        </div>
                      </div>
                    </div>
                </div>
            </div>
                   
            <div slot="footer">
                <div v-if="errorResponse" class="form-group">
                    <div class="row">
                        <div class="col-sm-12">
                            <strong>
                                <span style="white-space: pre; color: red;" v-html="errorResponse"></span>
                            </strong>
                        </div>
                    </div>
                </div>
                <button type="button" v-if="processingDetails" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Updating</button>
                <button type="button" v-else class="btn btn-default" @click="ok">Update</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>

<script>
import { api_endpoints, helpers, fetch_util } from "@/utils/hooks";
import utils from '@/components/internal/utils'
import modal from "@vue-utils/bootstrap-modal.vue";

import Vue from "vue";

export default {
  name: "Offender",
  data: function() {
    return {
      uuid: 0,
      errorResponse: null,
      processingDetails: false,
      isModalOpen: false,
      countries: [],
      offender_person: {
        first_name: "",
        last_name: "",
        dob: "",
        phone_number: "",
        mobile_number: "",
        address_street: "",
        address_locality: "",
        address_state: "",
        address_country: "",
        address_postcode: "",
      }
    }
  },
  props:{
    offender_id: {
      requird: true,
    },
    readonly: {
      default: true,
    }
  },
  components: {
    modal,
  },
  computed: {
    modalTitle: function() {
      return "Update Offender";
    },
  },
  methods: {
    sendData: async function() {
        let vm = this;
        let data = new FormData(); 
        data = {};
        data.first_name = vm.offender_person.first_name;
        data.last_name = vm.offender_person.last_name;
        data.dob = vm.offender_person.dob;
        data.phone_number = vm.offender_person.phone_number;
        data.mobile_number = vm.offender_person.mobile_number;
        data.address_street = vm.offender_person.address_street;
        data.address_locality = vm.offender_person.address_locality;
        data.address_state = vm.offender_person.address_state;
        data.address_country = vm.offender_person.address_country;
        data.address_postcode = vm.offender_person.address_postcode;
        let res = Vue.http.post(
            helpers.add_endpoint_join(
                api_endpoints.offenders,
                this.offender_id + "/update_offender_person/"),
                data
            );
        return res
    },
    ok: async function() {
        try {
            this.processingDetails = true;
            let response = await this.sendData();

            if (response.ok) {
                // Refresh offence table
                this.$nextTick(()=>{
                    this.$parent.$router.go()
                });
                this.close();
            }
        } catch(err) {
            this.processError(err);
            this.processingDetails = false;
        }
    },
    processError: async function(err) {
        let errorText = '';
        console.log(err)
        if (err.body){
            if (err.body.non_field_errors) {
                // When non field errors raised
                for (let i=0; i<err.body.non_field_errors.length; i++){
                    errorText += err.body.non_field_errors[i] + '<br />';
                }
            } else if(Array.isArray(err.body)) {
                // When general errors raised
                for (let i=0; i<err.body.length; i++){
                    errorText += err.body[i] + '<br />';
                }
            } else {
                // When field errors raised
                for (let field_name in err.body){
                    if (err.body.hasOwnProperty(field_name)){
                        errorText += field_name + ': ';
                        for (let j=0; j<err.body[field_name].length; j++){
                            errorText += err.body[field_name][j] + '<br />';
                        }
                    }
                }
            }
        } else {
            errorText += err.message;
        }
        this.errorResponse = errorText;
    },
    cancel: function() {
        this.processingDetails = false;
        this.close();
    },
    close: function() {
        this.processingDetails = false;
        this.isModalOpen = false;
    },
    loadCountries: function(){
        let vm = this;
        let initialisers = [
            utils.fetchCountries()
        ]
        Promise.all(initialisers).then(data => {
            vm.countries = data[0];
        });
    },
  },
  watch: {
    isModalOpen: function() {
        if (this.isModalOpen) {
            let initialisers = [utils.fetchOffender(this.offender_id)];
            Promise.all(initialisers).then(data => {
              this.offender_person = data[0];
            })
        }
    }
  },
  mounted() {
      let vm = this;
      vm.$nextTick(()=>{
          vm.loadCountries();
      })
  }  
};
</script>