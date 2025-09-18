<template lang="html">
    <div>
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
            <div class="container-fluid">
                <ul class="nav nav-pills">
                    <li class="nav-item active"><a data-toggle="tab" :href="'#'+oTab">Offence</a></li>
                    <li class="nav-item"><a data-toggle="tab" :href="'#'+dTab">Details</a></li>
                    <li class="nav-item"><a data-toggle="tab" :href="'#'+documentTab">Document</a></li>
                    <li class="nav-item"><a data-toggle="tab" :href="'#'+pTab">Offender(s)</a></li>
                    <li class="nav-item"><a data-toggle="tab" :href="'#'+lTab" @click="mapOffenceClicked">Location</a></li>
                </ul>
                <div class="tab-content">
                    <div :id="oTab" class="tab-pane fade in active">
                        <div class="row">

                            <div class="col-sm-12 form-group"><div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label float-start" for="offence-identifier">Identifier</label>
                                </div>
                                <div class="col-sm-6">
                                    <div v-if="offence">
                                        <input type="text" class="form-control" name="identifier" placeholder="" v-model="offence.identifier" v-bind:key="offence.id">
                                    </div>
                                </div>
                            </div></div>

                            <div class="col-sm-12 form-group"><div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label float-start">Region</label>
                                </div>
                                <div class="col-sm-7">
                                  <select class="form-control col-sm-9" v-on:change.prevent="offence.region_id=$event.target.value; updateDistricts('updateFromUI')" v-bind:value="offence.region_id">
                                    <option  v-for="option in regions" :value="option.id" v-bind:key="option.id">
                                      {{ option.name }} 
                                    </option>
                                  </select>
                                </div>
                            </div></div>

                            <div class="col-sm-12 form-group"><div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label float-start">District</label>
                                </div>
                                <div class="col-sm-7">
                                  <select class="form-control" v-model="offence.district_id">
                                    <option  v-for="option in availableDistricts" :value="option.district_id" v-bind:key="option.district_id">
                                      {{ option.district_name }} 
                                    </option>
                                  </select>
                                </div>
                            </div></div>

                            <div class="col-sm-12 form-group"><div class="row">
                                <label class="col-sm-3">Use occurrence from/to</label>
                                <input class="col-sm-1" id="occurrence_from_to_true" type="radio" v-model="offence.occurrence_from_to" v-bind:value="true">
                                <label class="col-sm-1 radio-button-label" for="occurrence_from_to_true">Yes</label>
                                <input class="col-sm-1" id="occurrence_from_to_false" type="radio" v-model="offence.occurrence_from_to" v-bind:value="false">
                                <label class="col-sm-1 radio-button-label" for="occurrence_from_to_false">No</label>
                            </div></div>

                            <div class="col-sm-12 form-group"><div class="row">
                                <label class="col-sm-3">{{ occurrenceDateLabel }}</label>
                                <div class="col-sm-3">
                                    <div class="input-group date" ref="occurrenceDateFromPicker">
                                        <input type="date" class="form-control" placeholder="DD/MM/YYYY" v-model="offence.occurrence_date_from" />
                                        <!--<span class="input-group-addon">
                                            <span class="glyphicon glyphicon-calendar"></span>
                                        </span>-->
                                    </div>
                                </div>
                                <label v-show="offence.occurrence_from_to" class="col-sm-1">to</label>
                                <div v-show="offence.occurrence_from_to">
                                    <div class="col-sm-3">
                                        <div class="input-group date" ref="occurrenceDateToPicker">
                                            <input type="date" class="form-control" placeholder="DD/MM/YYYY" v-model="offence.occurrence_date_to" />
                                            <!--<span class="input-group-addon">
                                                <span class="glyphicon glyphicon-calendar"></span>
                                            </span>-->
                                        </div>
                                    </div>
                                </div>
                            </div></div>

                            <div class="col-sm-12 form-group"><div class="row">
                                <label class="col-sm-3">{{ occurrenceTimeLabel }}</label>
                                <div class="col-sm-3">
                                    <div class="input-group date" ref="occurrenceTimeFromPicker">
                                        <input type="time" class="form-control" placeholder="HH:MM" v-model="offence.occurrence_time_from" />
                                        <!--<span class="input-group-addon">
                                            <span class="glyphicon glyphicon-calendar"></span>
                                        </span>-->
                                    </div>
                                </div>
                                <label v-show="offence.occurrence_from_to" class="col-sm-1">to</label>
                                <div v-show="offence.occurrence_from_to">
                                    <div class="col-sm-3">
                                        <div class="input-group date" ref="occurrenceTimeToPicker">
                                            <input type="time" class="form-control" placeholder="HH:MM" v-model="offence.occurrence_time_to" />
                                            <!--<span class="input-group-addon">
                                                <span class="glyphicon glyphicon-calendar"></span>
                                            </span>-->
                                        </div>
                                    </div>
                                </div>
                            </div></div>

                            <div class="col-sm-12 form-group"><div class="row">
                                <label class="col-sm-3">Alleged Offence</label>
                                <div class="col-sm-6">
                                    <input class="form-control" id="alleged-offence" />
                                </div>
                                <div class="col-sm-3">
                                    <input type="button" class="btn btn-primary" value="Add" @click.prevent="addAllegedOffenceClicked()" />
                                </div>
                            </div></div>

                            <div class="col-sm-12 form-group"><div class="row">
                                <div class="col-sm-12">
                                    <datatable ref="alleged_offence_table" id="alleged-offence-table" :dtOptions="dtOptionsAllegedOffence" :dtHeaders="dtHeadersAllegedOffence" />
                                </div>
                            </div></div>
                        </div>
                    </div>

                    <div :id="dTab" class="tab-pane fade in">
                        <div class="row">
                            <div class="col-sm-12">
                                <div class="form-group">
                                    <div class="row">
                                        <div class="col-sm-3">
                                            <label class="control-label float-start" for="offence-details">Details</label>
                                        </div>
                                        <div class="col-sm-6">
                                            <div v-if="offence">
                                                <textarea class="form-control" placeholder="add details" id="offence-details" v-model="offence.details" v-bind:key="offence.id"/>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div :id="documentTab" class="tab-pane face in">
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label float-start"  for="Name">Attachments</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <FileField 
                                            ref="comms_log_file" 
                                            name="comms-log-file" 
                                            :isRepeatable="true" 
                                            documentActionUrl="temporary_document" 
                                            @update-temp-doc-coll-id="setTemporaryDocumentCollectionId"
                                        />
                                    </div>
                                </div>
                            </div>
                    </div>

                    <div :id="pTab" class="tab-pane fade in">
                        <div class="row">
                          <div class="col-sm-12">
                            <div class="form-group">
                              <div class="row">
                                <div class="col-sm-12">
                                    <strong><label>Offender</label></strong>
                                  <div style="padding: 10px 5px; border: 1px solid lightgray;">
                                      <SearchOffender
                                        ref="search_offender"
                                        @entity-selected="personSelected"
                                        @clear-person="clearPerson"
                                        domIdHelper="search-offender"
                                        v-bind:key="updateSearchOffenderBindId"
                                        />
                                  </div>
                                </div>
                            </div>
                          </div>

                          <div class="form-group">
                            <div class="row">
                                <div class="col-sm-12">
                                    <input type="button" class="btn btn-primary" value="Add to Offender List" @click.prevent="addOffenderClicked()" />
                                </div>
                            </div>
                          </div>
                            <div class="form-group"><div class="row">
                                <div class="col-sm-12">
                                    <datatable ref="offender_table" id="offender-table" :dtOptions="dtOptionsOffender" :dtHeaders="dtHeadersOffender" />
                                </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div :id="lTab" class="tab-pane fade in">
                        <div class="row">
                            <div class="col-sm-12 form-group">
                                <div v-if="offence.location">
                                    <MapLocationOffence v-bind:key="lTab" :id="lTab" ref="mapOffenceComponent"/>
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
                <button type="button" v-if="processingDetails" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Adding</button>
                <button type="button" v-else class="btn btn-default" @click="ok">Ok</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>

<script>
import { v4 as uuid } from 'uuid';

import Awesomplete from "awesomplete";
import modal from "@/utils/vue/bootstrap-modal.vue";
import datatable from "@/utils/vue/datatable.vue";
import { mapGetters, mapActions } from "vuex";
import { api_endpoints, helpers, cache_helper, fetch_util } from "@/utils/hooks";
import MapLocationOffence from "./map_location_offence1.vue";
import SearchPersonOrganisation from "@/components/common/search_person_or_organisation.vue";
//import CreateNewPerson from "@/components/common/create_new_person.vue";
import utils from "../utils";
import $ from "jquery";

import "awesomplete/awesomplete.css";
import { v4 as uuidv4 } from 'uuid';
// import "jquery-ui/ui/widgets/draggable.js";
import FileField from '@common-components/compliance_file.vue';
import { data } from "jquery";
import SearchOffender from './search_offenders.vue'

export default {
  name: "Offence",
  data: function() {
    let vm = this;

    vm.max_items = 20;
    vm.ajax_for_alleged_offence = null;
    vm.ajax_for_offender = null;
    vm.suggest_list = []; // This stores a list of alleged offences displayed after search.
    vm.suggest_list_offender = []; // This stores a list of alleged offences displayed after search.
    vm.awe = null;

    return {
      uuid: 0,
      offender_count: 0,
      displayCreateNewPerson: false,
      updatingContact: false,
      newPersonBeingCreated: false,
      officers: [],
      isModalOpen: false,
      processingDetails: false,
      current_alleged_offence: {
        id: null,
        act: "",
        section_regulation: "",
        offence_text: ""
      },
      current_offender: null,
      offender_search_type: "individual",
      oTab: "oTab" + uuid(),
      dTab: "dTab" + uuid(),
      pTab: "pTab" + uuid(),
      lTab: "lTab" + uuid(),
      documentTab: 'documentTab' + uuid(),
      errorResponse: '',

      temporary_document_collection_id: null,

      // regionDistricts: [],
      regions: [], // this is the list of options
      availableDistricts: [], // this is generated from the regionDistricts[] above

      dtHeadersOffender: ["id", "Individual/Organisation", "Details", "Action"],
      dtHeadersAllegedOffence: [
        "id",
        "Act",
        "Section/Regulation",
        "Alleged Offence",
        "Action"
      ],
      dtOptionsOffender: {
        columns: [
          {
            data: "person_id",
            visible: false
          },
          {
            data: "data_type",
            visible: true
          },
          {
            data: "data_type",
            render: function(data, type, row) {
              if (row.data_type == "individual") {
                let full_name = [row.first_name, row.last_name]
                  .filter(Boolean)
                  .join(" ");
                let email = row.email ? "E:" + row.email : "";
                let p_number = row.phone_number ? "P:" + row.phone_number : "";
                let m_number = row.mobile_number
                  ? "M:" + row.mobile_number
                  : "";
                let dob = row.dob ? "DOB:" + row.dob : "DOB: ---";
                let myLabel = [
                  "<strong>" + full_name + "</strong>",
                  email,
                  p_number,
                  m_number,
                  dob
                ]
                  .filter(Boolean)
                  .join("<br />");

                return myLabel;
              } else if (row.data_type == "organisation") {
                let name = row.name ? row.name : "";
                let abn = row.abn ? "ABN:" + row.abn : "";
                let myLabel = ["<strong>" + name + "</strong>", abn]
                  .filter(Boolean)
                  .join("<br />");

                return myLabel;
              }
            }
          },
          {
            data: "person_id",
            render: function(data, type, row) {
              return (
                '<a href="#" class="remove_button" data-offender-num="' +
                row.num +
                '">Remove</a>'
              );
            }
          }
        ]
      },
      dtOptionsAllegedOffence: {
        columns: [
      //    {
      //      data: "id",
      //      visible: false
      //    },
      //    {
      //      data: "Act"
      //    },
      //    {
      //      data: "Section/Regulation"
      //    },
      //    {
      //      data: "Alleged Offence"
      //    },
      //    {
      //      data: "Action",
      //      mRender: function(data, type, row) {
      //        return (
      //          '<a href="#" class="remove_button" data-alleged-offence-id="' +
      //          row.id +
      //          '">Remove</a>'
      //        );
      //      }
      //    }
                    {
                        visible: false,
                        data: 'allegedOffence',
                        render: function(data, type, row) {
                            return row.allegedOffence.id;
                        }
                    },
                    {
                        data: 'allegedOffence',
                        render: function(data, type, row) {
                            let ret_str = row.allegedOffence.section_regulation.act;
                            return ret_str;
                        }
                    },
                    {
                        data: 'allegedOffence',
                        render: function(data, type, row) {
                            let ret_str = row.allegedOffence.section_regulation.name;
                            return ret_str;
                        }
                    },
                    {
                        data: 'allegedOffence',
                        render: function(data, type, row) {
                            let ret_str = row.allegedOffence.section_regulation.offence_text;
                            return ret_str;
                        }
                    },
                    {
                        data: 'allegedOffence',
                        render: function(data, type, row) {
                            let ret_str = '<a href="#" class="remove_button" data-alleged-offence-uuid="' + row.allegedOffence.uuid + '">Remove</a>';
                            return ret_str;
                        }
                    },
        ]
      }
    };

  },
  components: {
      modal,
      datatable,
      MapLocationOffence,
      SearchPersonOrganisation,
      FileField,
      SearchOffender,
  },
    props:{
      region_id: {
          required: false,
          default: null,
      },
      district_id: {
          required: false,
          default: null,
      },
      // allocated_group_id: {
      //     required: false,
      //     default: null,
      // },
  },
  computed: {
    ...mapGetters("offenceStore", {
      offence: "offence"
    }),
    ...mapGetters('inspectionStore', {
      inspection: "inspection",
    }),
    ...mapGetters('legalCaseStore', {
      legal_case: "legal_case",
    }),
    ...mapGetters('callemailStore', {
      call_email: "call_email",
    }),
    parent_legal_case: function() {
        if (this.legal_case && this.legal_case.id) {
            return true;
        }
    },
    parent_call_email: function() {
        if (this.call_email && this.call_email.id) {
            return true;
        }
    },
    parent_inspection: function() {
        if (this.inspection && this.inspection.id) {
            return true;
        }
    },

    modalTitle: function() {
      return "Identify Offence";
    },
    occurrenceDateLabel: function() {
      if (this.offence.occurrence_from_to) {
        return "Occurrence date from";
      } else {
        return "Occurrence date";
      }
    },
    occurrenceTimeLabel: function() {
      if (this.offence.occurrence_from_to) {
        return "Occurrence time from";
      } else {
        return "Occurrence time";
      }
    },
    updateSearchOffenderBindId: function() {
        this.uuid += 1
        return 'offender' + this.uuid
    },
    parentEntity: function() {
        return {'id': 1, 'data_type': 'individual'}
    },
  },
  methods: {
    ...mapActions("offenceStore", {
      setAllegedOffenceIds: "setAllegedOffenceIds",
      setOffenders: "setOffenders",
      setCallEmailId: "setCallEmailId",
      setRegionId: "setRegionId",
      setDistrictId: "setDistrictId",
      // setAllocatedGroupId: "setAllocatedGroupId",
      setInspectionId: "setInspectionId",
      setLegalCaseId: "setLegalCaseId",
      createOffence: "createOffence",
      setOffenceEmpty: "setOffenceEmpty",
      setTempDocumentCollectionId: "setTempDocumentCollectionId",
    }),
    ...mapActions('inspectionStore', {
      loadInspection: "loadInspection",
    }),
    ...mapActions('callemailStore', {
      loadCallEmail: "loadCallEmail",
    }),
    ...mapActions('legalCaseStore', {
      loadLegalCase: "loadLegalCase",
    }),
        setTemporaryDocumentCollectionId: function(val) {
            this.temporary_document_collection_id = val;
        },
    // makeModalsDraggable: function(){
    //     this.elem_modal = $('.modal > .modal-dialog');
    //     for (let i=0; i<this.elem_modal.length; i++){
    //         //$(this.elem_modal[i]).draggable();
    //     }
    // },
    constructRegionsAndDistricts: async function() {
        let returned_regions = await cache_helper.getSetCacheList(
            "Regions",
            "/api/regions/"
        );
        Object.assign(this.regions, returned_regions);
        this.regions.splice(0, 0, {
            id: "",
            name: "",
            district: "",
            districts: [],
            region: null
        });
        // let returned_region_districts = await cache_helper.getSetCacheList(
        //     "RegionDistricts",
        //     api_endpoints.region_district
        // );
        // Object.assign(this.regionDistricts, returned_region_districts);
    },
    personSelected: function(para) {
        let vm = this;
        vm.setCurrentOffender(para.data_type, para.id, para.source);
    },
    clearPerson: function(para) {
        let vm = this;
        vm.setCurrentOffender('', 0, '');
    },
    setCurrentOffender: function(data_type, id, source) {
      let vm = this;
      if (!id) {
          vm.current_offender = null;
      } else if (source == "offenders") {
        let initialisers = [utils.fetchOffender(id)];
        Promise.all(initialisers).then(data => {
          vm.current_offender = data[0];
          vm.current_offender.residential_address = {
                line1: data[0].address_street,
                locality: data[0].address_locality,
                state: data[0].address_state,
                country: data[0].address_country,
                postcode: data[0].address_postcode,
          }
          vm.current_offender.data_type = "individual";
          vm.current_offender.source = source;
        });
      } else if (source == "email_users") {
          vm.current_offender = {};
          vm.current_offender.data_type = "individual";
          vm.current_offender.source = source;
      }
    },
    setCurrentOffenderEmpty: function() {
        this.current_offender = {};
        $("#offender_input").val("");
        this.$refs.search_offender.clearInput();
    },
    removeOffenderClicked: function(e) {
      let vm = this;

      let offenderNum = parseInt(e.target.getAttribute("data-offender-num"));
      let remove_idx;
      vm.$refs.offender_table.vmDataTable.rows(function(idx, data, node) {
        if (data.num === offenderNum) {
          remove_idx = (idx); 
        }
      });
      vm.$refs.offender_table.vmDataTable
            .row(remove_idx)
            .remove()
            .draw();
    },
    removeClicked: function(e) {
            let alleged_offence_uuid = e.target.getAttribute("data-alleged-offence-uuid");

            // Remove offender
            for (let i=0; i<this.offence.alleged_offences.length; i++){
                let alleged_offence = this.offence.alleged_offences[i];
                if (alleged_offence.uuid == alleged_offence_uuid){
                    if (alleged_offence.id){
                        // this alleged_offence exists in the database
                        alleged_offence.removed = true;
                    } else {
                        // this is new alleged_offence
                        this.offence.alleged_offences.splice(i, 1);
                    }
                }
            }
            this.constructAllegedOffencesTable();
    //    let vm = this;

    //    let allegedOffenceId = parseInt(
    //      e.target.getAttribute("data-alleged-offence-id")
    //    );
    //    vm.$refs.alleged_offence_table.vmDataTable.rows(function(
    //      idx,
    //      data,
    //      node
    //    ) {
    //      if (data.id === allegedOffenceId) {
    //        vm.$refs.alleged_offence_table.vmDataTable
    //          .row(idx)
    //          .remove()
    //          .draw();
    //      }
    //    });
    },
    createNewPersonClicked: function() {
      let vm = this;
      vm.newPersonBeingCreated = true;
      vm.displayCreateNewPerson = !vm.displayCreateNewPerson;
    },
    cancelCreateNewPersonClicked: function() {
      let vm = this;
      vm.newPersonBeingCreated = false;
    },
    saveNewPersonClicked: function() {
      let vm = this;
      vm.newPersonBeingCreated = false;
    },
    addOffenderClicked: async function() {
      console.log("addOffenderClicked")
      let vm = this;
      this.errorResponse = "";

      let current_offender;
      if (
          (vm.current_offender == null || vm.current_offender.source == 'email_users') 
          && this.$refs.search_offender.displayCreateOffender
          && this.$refs.search_offender.$refs.search_users.displayUpdateCreatePerson
      ) {
          current_offender = this.$refs.search_offender.$refs.search_users.$refs.update_create_person.email_user;
      } else {
          current_offender = vm.current_offender;
      }

      let address = {};
      let missing = false;
      if (!(current_offender && 'residential_address' in current_offender)) {          
          missing = true;
      } else {
          address = current_offender.residential_address;
          let required_fields = [current_offender.first_name, current_offender.last_name, current_offender.dob, address.line1, address.locality, address.state, address.country, address.postcode];
          required_fields.forEach(field => {
                if (!field) {
                    missing = true;
                }
            });
      }
      if (
        current_offender && !missing
      ) {
        //NOTE: we assume individual if data type not specified
        if ((!('data_type' in current_offender) || current_offender.data_type !== undefined) || current_offender.data_type == "individual") {
          vm.offender_count++;          
          let person_id = 'new'
          //if from an existing offender person, set id to the id of that offender
          if (vm.current_offender != null && vm.current_offender.source == 'offenders') {
              person_id = current_offender.id;
          }
          vm.$refs.offender_table.vmDataTable.row
            .add({
              person_id: person_id,
              data_type: "individual",
              num: vm.offender_count,
              first_name: current_offender.first_name,
              last_name: current_offender.last_name,
              email: current_offender.email,
              p_number: current_offender.phone_number,
              m_number: current_offender.mobile_number,
              dob: current_offender.dob,
              residential_address: current_offender.residential_address
            })
            .draw();
            this.setCurrentOffenderEmpty();
            this.uuid++;
        }  
      } else if (current_offender && missing) {
          this.errorResponse = "Name, Address, and Date of Birth Required";
          console.log(this.errorResponse)
      }
        //TODO do we need org offenders?
        /*else if (current_offender.data_type == "organisation") {
          vm.offender_count++;
          vm.$refs.offender_table.vmDataTable.row
            .add({
              data_type: "organisation",
              id: vm.offender_count,
              name: current_offender.name,
              abn: current_offender.abn
            })
            .draw();
        }*/
        
    },
    addAllegedOffenceClicked: function() {
        if (this.current_alleged_offence && this.current_alleged_offence.id) {

            // Check if the item is already in the list
            let already_exists = false;
            for (let i=0; i<this.offence.alleged_offences.length; i++){
                let alleged_offence = this.offence.alleged_offences[i];
                if(alleged_offence.section_regulation.id == this.current_alleged_offence.id){
                    already_exists = true;
                }
            }

            if (!already_exists) {
                let alleged_offence_obj = {
                    id: '', 
                    removed: false, 
                    reason_for_removal: '', 
                    removed_by_id: null,
                    section_regulation: {},
                    number_linked_sanction_outcomes_total: 0,
                    number_linked_sanction_outcomes_active: 0,
                    uuid: uuidv4()
                };
                Object.assign(alleged_offence_obj.section_regulation, this.current_alleged_offence);
                this.offence.alleged_offences.push(alleged_offence_obj);
            }
        }
        this.setCurrentAllegedOffenceEmpty();
        this.constructAllegedOffencesTable();
    },
    constructAllegedOffencesTable: function(){
        this.$refs.alleged_offence_table.vmDataTable.clear().draw();
        if (this.offence.alleged_offences){
            for(let i=0; i<this.offence.alleged_offences.length; i++){
                this.addAllegedOffenceToTable(this.offence.alleged_offences[i]);
            }
        }
    },
    addAllegedOffenceToTable: function(allegedOffence){
        allegedOffence.uuid = uuidv4();
        this.$refs.alleged_offence_table.vmDataTable.row.add({ "allegedOffence": allegedOffence, "offence": this.offence }).draw();
    },
    ok: async function() {
        try {
            this.processingDetails = true;
            let response = await this.sendData();

            if (response.ok) {
                // Refresh offence table on the dashboard page
                if (this.$parent.$refs.offence_table){
                    this.$parent.$refs.offence_table.vmDataTable.ajax.reload();
                }

                // For Related items table
                if (this.parent_call_email) {
                    await this.loadCallEmail({
                        call_email_id: this.call_email.id,
                    });
                } else if (this.parent_legal_case) {
                    await this.loadLegalCase({
                        legal_case_id: this.legal_case.id,
                    });
                } else if (this.parent_inspection) {
                    await this.loadInspection({
                        inspection_id: this.inspection.id,
                    });
                }
            }

            if (this.$parent.$refs.related_items_table) {
                this.$parent.constructRelatedItemsTable();
            }

            this.setOffenceEmpty();
            this.close();
        } catch(err) {
            this.processError(err);
        } finally {
            this.processingDetails = false;
        }
    },
    processError: async function(err) {
        let errorText = '';
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
        // for call_email offenceBindId
        if (this.$parent.call_email) {
            this.$parent.updateUuid();
        }

        this.processingDetails = false;
        this.close();
    },
    close: function() {
        this.processingDetails = false;
        this.isModalOpen = false;
    //    this.setOffenceEmpty();  // Make offence default
        //this.constructAllegedOffencesTable();
        //this.errorResponse = '';
    },
    mapOffenceClicked: function() {
      this.$refs.mapOffenceComponent.mapTabClicked();
    },
    sendData: async function() {
        let vm = this;

        // If exists, set call_email_id and other attributes to the offence
        if (this.$parent.call_email && this.$parent.call_email.id) {
            vm.setCallEmailId(this.$parent.call_email.id);
        }

        // If exists, set inspection_id to the offence
        if (this.$parent.inspection && this.$parent.inspection.id) {
            vm.setInspectionId(this.$parent.inspection.id);
        }

        // If exists, set legal_case_id to the offence
        if (this.$parent.legal_case && this.$parent.legal_case.id) {
            vm.setLegalCaseId(this.$parent.legal_case.id);
        }

        if (this.temporary_document_collection_id){
            vm.setTempDocumentCollectionId(this.temporary_document_collection_id)
        }

        // Collect offenders data from the datatable, and set them to the vuex
        let offenders = vm.$refs.offender_table.vmDataTable.rows().data().toArray();

        //TODO fix to include all offender details
        console.log(offenders)
        vm.setOffenders(offenders);

        let res = await vm.createOffence();;
        return res
    },
    addEventListeners: function() {
      let vm = this;

      $("#alleged-offence-table").on(
        "click",
        ".remove_button",
        vm.removeClicked
      );
      $("#offender-table").on(
        "click",
        ".remove_button",
        vm.removeOffenderClicked
      );
    },
    search: function(searchTerm) {
      var vm = this;
      vm.suggest_list = [];
      vm.suggest_list.length = 0;
      vm.awe.list = [];

      /* Cancel all the previous requests */
      if (vm.ajax_for_alleged_offence != null) {
        vm.ajax_for_alleged_offence.abort();
        vm.ajax_for_alleged_offence = null;
      }

      vm.ajax_for_alleged_offence = $.ajax({
        type: "GET",
        url: "/api/search_alleged_offences/?search=" + searchTerm,
        success: function(data) {
          if (data && data.results) {
            let persons = data.results;
            let limit = Math.min(vm.max_items, persons.length);
            for (var i = 0; i < limit; i++) {
              vm.suggest_list.push(persons[i]);
            }
          }

          vm.awe.list = vm.suggest_list;
          vm.awe.evaluate();
        },
        error: function(e) {}
      });
    },
    markMatchedText(original_text, input) {
      let ret_text = original_text.replace(new RegExp(input, "gi"), function(
        a,
        b
      ) {
        return "<mark>" + a + "</mark>";
      });
      return ret_text;
    },
    initAwesompleteAllegedOffence: function() {
      var self = this;

      var element_search = document.getElementById("alleged-offence");
      self.awe = new Awesomplete(element_search, {
        maxItems: self.max_items,
        sort: false,
        filter: () => {
          return true;
        }, // Display all the items in the list without filtering.
        item: function(text, input) {
          let ret = Awesomplete.ITEM(text, ""); // Not sure how this works but this doesn't add <mark></mark>
          return ret;
        },
        data: function(item, input) {
          let act = item.act ? item.act : "";
          let name = item.name ? item.name : "";
          let offence_text = item.offence_text ? item.offence_text : "";

          let act_marked = self.markMatchedText(act, input);
          let name_marked = self.markMatchedText(name, input);
          let offence_text_marked = self.markMatchedText(offence_text, input);

          let myLabel = [
            "<strong>" + act_marked + ", " + name_marked + "</strong>",
            offence_text_marked
          ]
            .filter(Boolean)
            .join("<br />");
          myLabel = '<div data-item-id="' + item.id + '">' + myLabel + "</div>";

          return {
            label: myLabel, // Displayed in the list below the search box
            value: [act, name, offence_text].filter(Boolean).join(", "), // Inserted into the search box once selected
            id: item.id
          };
        }
      });
      $(element_search)
        .on("keyup", function(ev) {
          var keyCode = ev.keyCode || ev.which;
          if (
            (48 <= keyCode && keyCode <= 90) ||
            (96 <= keyCode && keyCode <= 105) ||
            keyCode == 8 ||
            keyCode == 46
          ) {
            self.search(ev.target.value);
            return false;
          }
        })
        .on("awesomplete-selectcomplete", function(ev) {
          ev.preventDefault();
          ev.stopPropagation();
          return false;
        })
        .on("awesomplete-select", function(ev) {
            /* Retrieve element id of the selected item from the list
             * By parsing it, we can get the order-number of the item in the list
             * 
             * Structure of the awesomplete list
             * <ul>
             *     <li>
             *         <div data-item-id="id_number">
             *             <strong>
             *                 <mark>
             * User can click either <li>/<div>/<strong>/<mark>.
             * Therefore to get the <div> element, which has an item id, you need a bit of calculation.
             */
            let origin = $(ev.originalEvent.origin);
            let originTagName = origin[0].tagName;
            switch(originTagName){
                case "STRONG":
                    origin = origin.parent();
                    break;
                case "MARK":
                    origin = origin.parent().parent();
                    break;
                case "LI":
                    origin = origin.children().first();
                    break;
            }
            let elem_id = origin[0].getAttribute("data-item-id");
            for (let i = 0; i < self.suggest_list.length; i++) {
                if (self.suggest_list[i].id == parseInt(elem_id)) {
                    self.setCurrentOffenceSelected(self.suggest_list[i]);
                    break;
                }
            }
        });
    },
    searchOrganisation: function(id) {
      return new Promise((resolve, reject) => {
        let request = fetch_util.fetchUrl("/api/search_organisation/" + id)
        request.then((response) => {
            resolve(response);
        }).catch((error) => {
            reject(error);
        });
      });
    },
    setCurrentOffenceSelected: function(offence) {
      let vm = this;

      if (offence.id) {
        vm.current_alleged_offence.id = offence.id;
        vm.current_alleged_offence.act = offence.act;
        vm.current_alleged_offence.name = offence.name;
        vm.current_alleged_offence.offence_text = offence.offence_text;
      } else {
        vm.setCurrentAllegedOffenceEmpty();
      }
    },
    setCurrentAllegedOffenceEmpty: function() {
      let vm = this;

      vm.current_alleged_offence.id = null;
      vm.current_alleged_offence.act = "";
      vm.current_alleged_offence.name = "";
      vm.current_alleged_offence.offence_text = "";

      $("#alleged-offence").val("");
    },
    currentRegionIdChanged: function() {
      this.updateDistricts();
    },
    updateDistricts: function(updateFromUI) {
      if (updateFromUI) {
        // We don't want to clear the default district selection when initially loaded, which derived from the call_email
        this.offence.district_id = null;
      }

      this.availableDistricts = []; // This is a list of options for district
      for (let region of this.regions) {
        if (region.id == this.offence.region_id) {
          this.availableDistricts = region.districts
        }
      }

      this.availableDistricts.splice(0, 0, {
        district_id: "",
        district_name: "",
        district: "",
        districts: [],
        region: null
      });
    },
  },
    created: async function() {

        let self = this;
        self.setOffenceEmpty();
        self.$nextTick(function() {
            self.initAwesompleteAllegedOffence();
        });
        await this.constructRegionsAndDistricts();
        this.setRegionId(this.region_id);
        this.setDistrictId(this.district_id);
        // this.setAllocatedGroupId(this.allocated_group_id);
    },
    mounted: function() {
        this.$nextTick(() => {
            this.addEventListeners();
            // this.makeModalsDraggable();
        });
    }
};
</script>

<style lang="css" scoped>
.btn-file {
  position: relative;
  overflow: hidden;
}
.btn-file input[type="file"] {
  position: absolute;
  top: 0;
  right: 0;
  min-width: 100%;
  min-height: 100%;
  font-size: 100px;
  text-align: right;
  filter: alpha(opacity=0);
  opacity: 0;
  outline: none;
  background: white;
  cursor: inherit;
  display: block;
}
.top-buffer {
  margin-top: 5px;
}
.top-buffer-2x {
  margin-top: 10px;
}
#offence-details {
}
.radio-button-label {
  padding-left: 0;
}
.tab-content {
  background: white;
  padding: 10px;
  border: solid 1px lightgray;
}
#DataTable {
  padding: 10px 5px;
  border: 1px solid lightgray;
}
</style>
