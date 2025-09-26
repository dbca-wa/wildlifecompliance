<template>
  <FormSection
      :form-collapse="false"
      label="Return"
      index="return"
  >
    <div class="card-body">
    <AmendmentRequestDetails v-show="is_external"/>
        <div class="col-md-12" v-if="returns.has_species">
            <div class="form-group">
                <label class="fw-bold" for="">Species Available:</label>
                <select class="form-control" ref="selected_species" v-model="returns.species">
                    <option class="change-species" v-for="(specie, s_idx) in returns.species_list" :value="s_idx" :species_id="s_idx" v-bind:key="`specie_${s_idx}`" >{{specie}}</option>
                </select>
            </div>
        </div>
        <div class="col-sm-12">
            <div class="row form-group">
                <label class="fw-bold">Do you want to Lodge a nil Return?</label>
                <div class="col-md-3">
                <input type="radio" id="nilYes" name="nilYes" value="yes" v-model='returns.nil_return' :disabled='isReadOnly'>
                <label for="nilYes">Yes</label>
                </div>
                <div class="col-md-3">
                <input type="radio" id="nilNo" name="nilNo" value="no" v-model='returns.nil_return' :disabled='isReadOnly'>
                <label for="nilNo">No</label>
                </div>
            </div>
            <div v-if="nilReturn === 'yes'" class="row form-group">
                <label class="col-sm-4">Reason for providing a Nil return.</label>
                <input type="textarea" name="nilReason" v-model="returns.nilReason">
            </div>
            <div v-if="nilReturn === 'no'" class="row form-group">
                <label class="fw-bold">Do you want to upload spreadsheet with Return data?<br>(Download <a v-bind:href="returns.template">spreadsheet template</a>)</label>
                <div class="col-md-3">
                <input type="radio" name="SpreadsheetYes" value="yes" v-model='spreadsheetReturn' :disabled='isReadOnly'>
                <label for="SpreadsheetYes">Yes</label>
                </div>
                <div class="col-md-3">
                <input type="radio" name="SpreadsheetNo" value="no" v-model='spreadsheetReturn' :disabled='isReadOnly' >
                <label for="SpreadsheetNo">No</label>
                </div>
            </div>
            <div v-if="nilReturn === 'no' && spreadsheetReturn === 'yes'" class="row form-group">
                <label class="col-sm-4 fw-bold">Do you want to add to existing data or replace existing data?</label>
                <div class="col-md-3">
                <input type="radio" name="ReplaceYes" value="yes" v-model='replaceReturn' :disabled='isReadOnly'>
                <label for="ReplaceYes">Replace</label>
                </div>
                <div class="col-md-3">
                <input type="radio" name="ReplaceNo" value="no" v-model='replaceReturn' :disabled='isReadOnly'>
                <label for="ReplaceNo">Add to</label>
                </div>
            </div>
            <div v-if="nilReturn === 'no' && spreadsheetReturn === 'yes'" class="row form-group">
                <div class="col-md-3">
                <span class="btn btn-primary btn-file float-start">Upload File
                    <input type="file" ref="spreadsheet" @change="uploadFile()"/>
                </span>
                </div>
                <div class="col-md-6">
                <span class="float-start" style="margin-left:10px;margin-top:10px;">{{uploadedFileName}}</span>
                </div>
            </div>
            <div class="row"></div>
            <div v-if="refreshGrid && nilReturn === 'no'" class="row">
                <renderer-block v-for="(data, key) in returns.table"
                          :component="data"
                          v-bind:key="`returns-grid-data_${key}`"
                /></br>
            </div>
            <div class="margin-left-20"></div>
            <!-- End of Spreadsheet Return -->
        </div>
    </div>
    <input type='hidden' name="table_name" :value="returns.table[0].name" />
  </FormSection>
</template>

<script>
import { v4 as uuid } from 'uuid';
import { mapActions, mapGetters } from 'vuex'
import AmendmentRequestDetails from './return_amendment.vue';
import {
  api_endpoints,
  helpers, fetch_util
}
from '@/utils/hooks'

import FormSection from "@/components/forms/section_toggle.vue";
export default {
  name: 'externalReturn',
  props:["table", "data", "grid"],
  data() {
    let vm = this;
    return {
        pdBody: 'pdBody' + uuid(),
        form: null,
        spreadsheet: null,
        returnBtn: 'Submit',
        nilReturn: 'yes',
        spreadsheetReturn: 'no',
        replaceReturn: 'no',
        readonly: false,
        refresh_grid: true,
    }
  },
  components: {
    FormSection,
    AmendmentRequestDetails,
  },
  computed: {
     ...mapGetters([
        'isReturnsLoaded',
        'returns',
        'is_external',
        'species_cache',
    ]),
    uploadedFileName: function() {
      return this.spreadsheet != null ? this.spreadsheet.name: '';
    },
    isReadOnly: function() {
      this.readonly = this.is_external && this.returns.is_draft ? false : true;
      return this.readonly;
    },
    refreshGrid: function() {
      this.setReturnsEstimateFee()
      // update cached for uploaded data.
      // this.getSpecies(this.returns.species)
      this.species_cache[this.returns.species] = this.returns.table[0]['data']
      return this.refresh_grid;
    }
  },
  methods: {
    ...mapActions({
      load: 'loadReturns',
    }),
    ...mapActions([
        'setReturns',
        'setReturnsEstimateFee',
    ]),
    uploadFile: function(e) {
      let _file = null;
      var input = $(this.$refs.spreadsheet)[0];
      if (input.files && input.files[0]) {
        var reader = new FileReader();
        reader.readAsDataURL(input.files[0]);
        reader.onload = function(e) {
          _file = e.target.result;
        };
        _file = input.files[0];
      }
      this.spreadsheet = _file;
      this.validate_upload()
    },
    validate_upload: async function(e) {
      this.refresh_grid = false
      let _data = new FormData(this.form);
      _data.append('spreadsheet', this.spreadsheet)
      let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.returns,this.returns.id+'/upload_details'),{method:'POST', body:JSON.stringify(_data)},{
                    emulateJSON:true,
        })
      request.then((response)=>{
            if (this.replaceReturn === 'no') {
              let idx1 = this.returns.table[0]['data'].length
              for (let idx2=0; idx2 < response[0]['data'].length; idx2++) {
                this.returns.table[0]['data'][idx1++] = response[0]['data'][idx2]
              }
            }
            if (this.replaceReturn === 'yes') {
              this.returns.table[0]['data'] = response[0]['data']
              this.replaceReturn = 'no'
            }
            this.species_cache[this.returns.species] = this.returns.table[0]['data']
            this.nilReturn = 'no'
            this.spreadsheetReturn = 'yes'
            this.refresh_grid = true
        },exception=>{
		        swal.fire('Error Uploading', helpers.apiVueResourceError(), 'error');
        });
    },
    getSpecies: async function(_id){
      var specie_id = _id

      if (this.species_cache[this.returns.species]==null) {
        // cache currently displayed species json
        this.species_cache[this.returns.species] = this.returns.table[0]['data']
      }

      if (this.species_cache[specie_id] != null) {
        // species json previously loaded from ajax
        this.returns.table[0]['data'] = this.species_cache[specie_id]
        this.setGridDate(specie_id)

      } else {
        // load species json from ajax
        this.refresh_grid = false
        this.returns.species = specie_id
        let request = fetch_util.fetchUrl(helpers.add_endpoint_json(api_endpoints.returns,this.returns.id+'/species_data_details/?species_id='+specie_id+'&'))
        request.then((response)=>{
          this.returns.table[0]['data'] = response[0]['data']     
        }).catch((error) => {
          swal.fire('Error with Species data', helpers.apiVueResourceError(error), 'error');
        });
      };  // end 
      this.replaceReturn = 'no'
      this.nilReturn = 'no'
      this.spreadsheetReturn = 'no'
      this.returns.species = specie_id;
      this.refresh_grid = true
      return
    },
    setGridDate: function(_id){
        let specie_id = _id
        for (let r=0; r<this.species_cache[specie_id].length; r++){
          let val = 'date' + '::' + r;
          if ($(`[id='${val}']`)[0]){
            $(`[id='${val}']`)[0].value = this.species_cache[specie_id][r]['date']['value']
          } else {
            break;
          }
        } 
    },
    initialiseSpeciesSelect: function(reinit=false){
      var vm = this;
      if (reinit){
          $(vm.$refs.selected_species).data('select2') ? $(vm.$refs.selected_species).select2('destroy'): '';
      }
      
      $(vm.$refs.selected_species).select2({
          theme: "bootstrap",
          allowClear: true,
          placeholder: "Select..."
      }).
      on("select2:select",function (e) {
          e.stopImmediatePropagation();
          e.preventDefault();
          var selected = $(e.currentTarget);
          vm.getSpecies(selected.val());
      });
    },
    eventListeners: function () {
      var vm = this;
      this.initialiseSpeciesSelect();
      this.getSpecies(this.returns.species)
    }
  },
  mounted: function(){
    this.$nextTick(() => {
        this.form = document.forms.enter_return;
        this.readonly = !this.is_external;

        if (this.returns.table[0]) {
            this.nilReturn = 'no'
            this.spreadsheetReturn = 'no'
            this.replaceReturn = 'no'
        }

        this.eventListeners();
    });
  },
}
</script>
