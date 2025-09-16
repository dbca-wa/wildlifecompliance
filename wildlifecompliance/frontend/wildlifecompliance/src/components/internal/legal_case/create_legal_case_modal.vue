<template lang="html">
    <div id="CreateLegalCase">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" title="Create New Case" large force>
          <div class="container-fluid">
            <div class="row">
                <div class="col-sm-12">
                        <div class="form-group">
                          <div class="row">
                            <div class="col-sm-3">
                              <label>Region</label>
                            </div>
                            <div class="col-sm-9">
                              <select class="form-control col-sm-9" @change.prevent="updateDistricts()" v-model="region_id">
                                <option  v-for="option in regions" :value="option.id" v-bind:key="option.id">
                                  {{ option.name }} 
                                </option>
                              </select>
                            </div>
                          </div>
                        </div>
                        <div class="form-group">
                          <div class="row">
                            <div class="col-sm-3">
                              <label>District</label>
                            </div>
                            <div class="col-sm-9">
                              <select class="form-control" @change.prevent="updateAllocatedGroup()" v-model="district_id">
                                <option  v-for="option in availableDistricts" :value="option.district_id" v-bind:key="option.district_id">
                                  {{ option.district_name }} 
                                </option>
                              </select>
                            </div>
                          </div>
                        </div>
                        <div class="form-group">
                          <div class="row">
                            <div class="col-sm-3">
                              <label>Allocate to</label>
                            </div>
                            <div class="col-sm-9">
                              <select class="form-control" v-model="assigned_to_id">
                                <option  v-for="option in allocatedGroup" :value="option.id" v-bind:key="option.id">
                                  {{ option.full_name }} 
                                </option>
                              </select>
                            </div>
                          </div>
                        </div>
                        <div class="form-group">
                            <div class="row">
                                <div class="col-sm-3">
                                  <label>Title</label>
                                </div>
                                <div class="col-sm-9">
                                    <input type="text" class="form-control" v-model="legalCaseTitle" />
                                </div>
                            </div>
                        </div>

                        <div class="form-group">
                          <div class="row">
                            <div class="col-sm-3">
                              <label>Case priority</label>
                            </div>
                            <div class="col-sm-9">
                              <select class="form-control" v-model="legal_case_priority_id">
                                <option  v-for="option in legalCasePriorities" :value="option.id" v-bind:key="option.id">
                                  {{ option.case_priority }}
                                </option>
                              </select>
                            </div>
                          </div>
                        </div>

                        <div class="form-group">
                          <div class="row">
                              <div class="col-sm-3">
                                  <label class="control-label float-start" for="details">Details</label>
                              </div>
            			      <div class="col-sm-6">
                                  <textarea class="form-control" placeholder="add details" id="details" v-model="legalCaseDetails"/>
                              </div>
                          </div>
                        </div>
                        <div class="form-group">
                            <div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label float-start"  for="Name">Attachments</label>
                                </div>
            			        <div class="col-sm-9">
                                    <filefield 
                                    ref="comms_log_file" 
                                    name="comms-log-file" 
                                    :isRepeatable="true" 
                                    documentActionUrl="temporary_document" 
                                    @update-temp-doc-coll-id="setTemporaryDocumentCollectionId"/>
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
                                <span style="white-space: pre; color: red">{{ errorResponse }}</span>
                            </strong>
                        </div>
                    </div>
                </div>
                <button type="button" class="btn btn-default" @click="ok">Ok</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div>
        </modal>
    </div>
</template>
<script>
 "vue";
import modal from '@vue-utils/bootstrap-modal.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper, fetch_util } from "@/utils/hooks";
import filefield from '@common-components/compliance_file.vue';
import { required } from '@vuelidate/validators'

export default {
    name: "CreateInspection",
    data: function() {
      return {
            officers: [],
            isModalOpen: false,
            processingDetails: false,
            form: null,
            regions: [],
            // regionDistricts: [],
            availableDistricts: [],
            legalCasePriorities: [],
            externalOrganisations: [],
            legalCaseDetails: '',
            legalCaseTitle: '',
            errorResponse: "",
            region_id: null,
            district_id: null,
            assigned_to_id: null,
            advice_details: "",
            allocatedGroup: [],
            allocated_group_id: null,
            documentActionUrl: '',
            temporary_document_collection_id: null,
            legal_case_priority_id: null,
      }
    },
    components: {
      modal,
      filefield,
    },
    validations: {
        region_id: {
            required,
        },
        assigned_to_id: {
            required,
        },
        legal_case_priority_id: {
            required,
        },
    },
    computed: {
      ...mapGetters('legalCaseStore', {
        legal_case: "legal_case",
      }),
      ...mapGetters('callemailStore', {
        call_email: "call_email",
      }),
      parent_call_email: function() {
          if (this.call_email && this.call_email.id) {
              return true;
          }
      },
      // regionDistrictId: function() {
      //     if (this.district_id || this.region_id) {
      //         return this.district_id ? this.district_id : this.region_id;
      //     } else {
      //         return null;
      //     }
      // },
    },
    methods: {
      ...mapActions('legalCaseStore', {
          saveInspection: 'saveLegalCase',
          loadInspection: 'loadLegalCase',
          setInspection: 'setLegalCase',
      }),
      ...mapActions({
          loadAllocatedGroup: 'loadAllocatedGroup',
      }),
      ...mapActions('callemailStore', {
          loadCallEmail: 'loadCallEmail',
      }),
      setTemporaryDocumentCollectionId: function(val) {
          this.temporary_document_collection_id = val;
      },
      updateDistricts: function() {
        this.district_id = null;
        this.availableDistricts = [];
        for (let region of this.regions) {
          if (this.region_id === region.id) {
            this.availableDistricts=region.districts
          }
        }
        this.availableDistricts.splice(0, 0, 
        {
          id: "", 
          display_name: "",
          district: "",
          districts: [],
          region: null,
        });
        // ensure security group members list is up to date
        this.updateAllocatedGroup();
      },
      updateAllocatedGroup: async function() {
          this.errorResponse = "";
          if (this.region_id) {
              let allocatedGroupResponse = await this.loadAllocatedGroup({
                workflow_type: 'allocate_for_case',
                region_id: this.region_id,
                district_id: this.district_id ? this.district_id : null,
              });
              if (allocatedGroupResponse.ok) {
                  this.allocatedGroup = allocatedGroupresponse;
                  this.allocated_group_id = allocatedGroupresponse.group_id;
              } else {
                  // Display http error response on modal
                  this.errorResponse = allocatedGroupResponse.statusText;
              }
              // Display empty group error on modal
              if (!this.errorResponse &&
                  this.allocatedGroup &&
                  this.allocatedGroup.length <= 1) {
                  this.errorResponse = 'This group has no members';
              }
          } else {
              this.allocatedGroup = [];
          }
      },

      ok: async function () {
          let is_valid_form = this.isValidForm();
          if (is_valid_form) {
              const response = await this.sendData();
              if (response.ok) {
                  // For LegalCase Dashboard
                  if (this.$parent.$refs.legal_case_table) {
                      this.$parent.$refs.legal_case_table.vmDataTable.ajax.reload()
                  }
                  // For CallEmail related items table
                  if (this.parent_call_email) {
                      await this.loadCallEmail({
                          call_email_id: this.call_email.id,
                      });
                  }
                  if (this.$parent.$refs.related_items_table) {
                      this.$parent.constructRelatedItemsTable();
                  }
                  this.close();
                  //this.$router.push({ name: 'internal-inspection-dash' });
              }
          }
      },
      isValidForm: function() {
          this.$v.$touch();
          if (this.$v.$invalid) {
              this.errorResponse = 'Invalid form:\n';
              if (this.$v.region_id.$invalid) {
                  this.errorResponse += 'Region is required\n';
              }
              if (this.$v.assigned_to_id.$invalid) {
                  this.errorResponse += 'Officer must be assigned\n';
              }
              if (this.$v.legal_case_priority_id.$invalid) {
                  this.errorResponse += 'Choose Case Priority\n';
              }
              return false;
          } else {
              return true;
          }
      },
      cancel: async function() {
          await this.$refs.comms_log_file.cancel();
          this.isModalOpen = false;
          this.close();
      },
      close: function () {
          this.isModalOpen = false;
      },
      sendData: async function() {
          let post_url = '/api/legal_case/';

          let payload = new FormData();
          payload.append('details', this.legalCaseDetails);
          payload.append('title', this.legalCaseTitle);
          this.$refs.comms_log_file.commsLogId ? payload.append('legal_case_comms_log_id', this.$refs.comms_log_file.commsLogId) : null;
          this.parent_call_email ? payload.append('call_email_id', this.call_email.id) : null;
          this.district_id ? payload.append('district_id', this.district_id) : null;
          this.assigned_to_id ? payload.append('assigned_to_id', this.assigned_to_id) : null;
          this.inspection_type_id ? payload.append('legal_case_priority_id', this.legal_case_priority_id) : null;
          this.region_id ? payload.append('region_id', this.region_id) : null;
          this.allocated_group_id ? payload.append('allocated_group_id', this.allocated_group_id) : null;
          this.temporary_document_collection_id ? payload.append('temporary_document_collection_id', this.temporary_document_collection_id.temp_doc_id) : null;

          try {
              let res = await fetch_util.fetchUrl(post_url, {method:'POST', body:JSON.stringify(payload)});
              console.log(res);
              if (res.ok) {
                  return res
              }
          } catch(err) {
              console.log(err);
              this.errorResponse = 'Error:' + err.bodyText;
          }
          
      },
    },
    created: async function() {
        // regions
        let returned_regions = await cache_helper.getSetCacheList('Regions', '/api/regions/');
        Object.assign(this.regions, returned_regions);
        // blank entry allows user to clear selection
        this.regions.splice(0, 0, 
            {
              id: "", 
              display_name: "",
              district: "",
              districts: [],
              region: null,
            });
        // let returned_region_districts = await cache_helper.getSetCacheList(
        //     'RegionDistricts', 
        //     api_endpoints.region_district
        //     );
        // Object.assign(this.regionDistricts, returned_region_districts);

        // legal_case_priorities
        let returned_legal_case_priorities = await cache_helper.getSetCacheList(
            'LegalCasePriorities',
            api_endpoints.legal_case_priorities
            );
        Object.assign(this.legalCasePriorities, returned_legal_case_priorities);
        // blank entry allows user to clear selection
        this.legalCasePriorities.splice(0, 0, 
            {
              id: "", 
              description: "",
            });
        // If exists, get parent component details from vuex
        if (this.parent_call_email) {
             // Set regionId and districtId based on GIS lookup
          if (this.call_email && this.call_email.region_gis) {
              const region = this.regions.find(obj => obj.name === this.call_email.region_gis)
              if (region) {
                  this.region_id = region.id
                  if (this.call_email.district_gis) {
                      const district = region.districts.find(obj => obj.district_name === this.call_email.district_gis)
                      if (district) {
                          this.district_id = district.district_id
                      }
                  }
              }
          }
        }

        // If no Region/District selected, initialise region as Kensington
        // if (!this.regionDistrictId) {
        //     for (let record of this.regionDistricts) {
        //         if (record.district === 'KENSINGTON') {
        //             this.district_id = null;
        //             this.region_id = record.id;
        //         }
        //     }
        // }
        // ensure availableDistricts and allocated group is current
        this.updateDistricts();
        await this.updateAllocatedGroup();
    },
};
</script>

<style lang="css">
.btn-file {
    position: relative;
    overflow: hidden;
}
.btn-file input[type=file] {
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
.top-buffer{margin-top: 5px;}
.top-buffer-2x{margin-top: 10px;}
</style>
