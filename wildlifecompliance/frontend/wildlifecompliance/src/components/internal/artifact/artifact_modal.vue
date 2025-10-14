<template lang="html">
    <div id="ArtifactModal">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" title="Identify Object" large force>
          <div class="container-fluid">
            <div class="row">
                <div class="col-sm-12">
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

import modal from '@vue-utils/bootstrap-modal.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper, fetch_util } from "@/utils/hooks";
import filefield from '@common-components/compliance_file.vue';
import { required } from '@vuelidate/validators'

export default {
    name: "ArtifactModal",
    data: function() {
      return {
            officers: [],
            isModalOpen: false,
            processingDetails: false,
            form: null,
            regions: [],
            regionDistricts: [],
            availableDistricts: [],
            legalCasePriorities: [],
            externalOrganisations: [],
            legalCaseDetails: '',
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
      regionDistrictId: function() {
          if (this.district_id || this.region_id) {
              return this.district_id ? this.district_id : this.region_id;
          } else {
              return null;
          }
      },
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
        this.availableDistricts = [];
        for (let region of this.regions) {
          if (this.region_id === region.id) {
            this.availableDistricts=region.districts
          }
        }
        this.availableDistricts.splice(0, 0, 
        {
          district_id: "", 
          district_name: "",
          district: "",
          districts: [],
          region: null,
        });
        // ensure security group members list is up to date
        this.updateAllocatedGroup();
      },
      updateAllocatedGroup: async function() {
          console.log("updateAllocatedGroup");
          this.errorResponse = "";
          if (this.regionDistrictId) {
              let allocatedGroupResponse = await this.loadAllocatedGroup({
              region_district_id: this.regionDistrictId,
              group_permission: 'officer',
              });
              if (allocatedGroupResponse) {
                  console.log(allocatedGroupresponse.allocated_group);
                  this.allocatedGroup = allocatedGroupresponse.allocated_group;
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
              console.log(response);
              if (response) {
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
              }
          }
      },
      isValidForm: function() {
          console.log("performValidation");
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
          this.$refs.comms_log_file.commsLogId ? payload.append('legal_case_comms_log_id', this.$refs.comms_log_file.commsLogId) : null;
          this.parent_call_email ? payload.append('call_email_id', this.call_email.id) : null;
          this.district_id ? payload.append('district_id', this.district_id) : null;
          this.assigned_to_id ? payload.append('assigned_to_id', this.assigned_to_id) : null;
          this.inspection_type_id ? payload.append('legal_case_priority_id', this.legal_case_priority_id) : null;
          this.region_id ? payload.append('region_id', this.region_id) : null;
          this.allocated_group_id ? payload.append('allocated_group_id', this.allocated_group_id) : null;
          this.temporary_document_collection_id ? payload.append('temporary_document_collection_id', this.temporary_document_collection_id) : null;

          try {
              let res = await fetch_util.fetchUrl(post_url, {method:'POST', body:JSON.stringify(payload)});
              return res
              
          } catch(err) {
                  this.errorResponse = 'Error:' + err.statusText;
              }
          
      },
    },
    created: async function() {
        // regions
        let returned_regions = await cache_helper.getSetCacheList(
            "Regions",
            "/api/regions/"
        );        Object.assign(this.regions, returned_regions);
        // blank entry allows user to clear selection
        this.regions.splice(0, 0, 
            {
              id: "", 
              name: "",
              district: "",
              districts: [],
              region: null,
            });

        // inspection_types
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
            this.region_id = this.call_email.region_id;
            this.district_id = this.call_email.district_id;
        }

        // If no Region/District selected, initialise region as Kensington
        if (!this.regionDistrictId) {
            for (let record of this.regionDistricts) {
                if (record.district === 'KENSINGTON') {
                    this.district_id = null;
                    this.region_id = record.id;
                }
            }
        }
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
