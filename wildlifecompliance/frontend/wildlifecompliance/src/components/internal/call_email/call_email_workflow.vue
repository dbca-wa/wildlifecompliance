<template lang="html">
    <div id="CallWorkflow">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
          <div class="container-fluid">
            <div class="row">
                <div class="col-sm-12">
                        <div v-if="regionVisibility" class="form-group">
                          <div class="row">
                            <div class="col-sm-3">
                              <label>Region</label>
                            </div>
                            <div class="col-sm-9">
                              <select class="form-control col-sm-9" @change.prevent="updateDistricts()" v-model="region_id">
                                <option  v-for="option in regions" :value="option.id" v-bind:key="option.id">
                                  {{ option.display_name }} 
                                </option>
                              </select>
                            </div>
                          </div>
                        </div>
                        <div v-if="regionVisibility" class="form-group">
                          <div class="row">
                            <div class="col-sm-3">
                              <label>District</label>
                            </div>
                            <div class="col-sm-9">
                              <select class="form-control" @change.prevent="updateAllocatedGroup()" v-model="district_id">
                                <option  v-for="option in availableDistricts" :value="option.id" v-bind:key="option.id">
                                  {{ option.display_name }} 
                                </option>
                              </select>
                            </div>
                          </div>
                        </div>
                        <div v-if="allocateToVisibility" class="form-group">
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

                        <div v-if="workflow_type === 'close'" class="form-group">
                          <div class="row">
                            <div class="col-sm-3">
                              <label>Referred To</label>
                            </div>
                            <div class="col-sm-9">
                                <!--select multiple class="form-control" v-model="referrers_selected"-->
                                <select style="width:100%" class="form-control input-sm" multiple ref="referrerList">
                                    <option  v-for="option in referrers" :value="option.id" v-bind:key="option.id">
                                        {{ option.name }} 
                                    </option>
                              </select>
                            </div>
                          </div>
                        </div>

                        <div class="form-group">
                          <div class="row">
                              <div class="col-sm-3">
                                  <label class="control-label pull-left" for="details">Details</label>
                              </div>
            			      <div class="col-sm-6">
			                	  <textarea v-if="workflow_type === 'close'" class="form-control" placeholder="add details" id="details" v-model="advice_details"/>
                                  <textarea v-else class="form-control" placeholder="add details" id="details" v-model="workflowDetails"/>
                              </div>
                          </div>
                        </div>
                        <div class="form-group">
                            <div class="row">
                                <div class="col-sm-3">
                                    <label class="control-label pull-left"  for="Name">Attachments</label>
                                </div>
            			        <div class="col-sm-9">
                                    <filefield ref="comms_log_file" name="comms-log-file" :isRepeatable="true" :documentActionUrl="call_email.commsLogsDocumentUrl"  />
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
                                <span style="white-space: pre;">{{ errorResponse }}</span>
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
import Vue from "vue";
import modal from '@vue-utils/bootstrap-modal.vue';
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import filefield from '@/components/common/compliance_file.vue';
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import { required, minLength, between } from 'vuelidate/lib/validators'

export default {
    name: "CallEmailWorking",
    data: function() {
      return {
            officers: [],
            isModalOpen: false,
            processingDetails: false,
            form: null,
            regions: [],
            regionDistricts: [],
            availableDistricts: [],
            externalOrganisations: [],
            referrers: [],
            referrersSelected: [],
            workflowDetails: '',
            errorResponse: "",
            region_id: null,
            district_id: null,
            assigned_to_id: null,
            inspection_type_id: null,
            case_priority_id: null,
            advice_details: "",
            allocatedGroup: [],
            allocated_group_id: null,
            files: [
                    {
                        'file': null,
                        'name': ''
                    }
                ]
      }
    },
    components: {
      modal,
      filefield,
    },
    validations: function() {
        if (this.workflow_type === 'allocate_for_follow_up') {
            return {
                region_id: {
                    required,
                },
                assigned_to_id: {
                    required,
                },
            }
        } else if (this.workflow_type === 'close') {
            return {}
        } else {
            return {
                region_id: {
                    required,
                },
            }
        }
    },
    props:{
          workflow_type: {
              type: String,
              default: '',
          },
      },
    computed: {
      ...mapGetters('callemailStore', {
        call_email: "call_email",
      }),
      regionVisibility: function() {
        if (!(this.workflow_type === 'forward_to_wildlife_protection_branch' || 
          this.workflow_type === 'close')
        ) {
              return true;
        } else {
              return false;
        }
      },
      allocateToVisibility: function() {
          if (this.workflow_type.startsWith('allocate')) {
              return true;
        } else {
              return false;
        }
      },
      groupPermission: function() {
        if (this.workflow_type === 'forward_to_regions') {
            return 'triage_call_email';
        } else if (this.workflow_type === 'forward_to_wildlife_protection_branch') {
              return 'triage_call_email';
        } else if (this.workflow_type === 'allocate_for_follow_up') {
              return 'officer';
        } else if (this.workflow_type === 'allocate_for_inspection') {
              return 'officer';
        } else if (this.workflow_type === 'allocate_for_case') {
              return 'officer';
        } else if (this.workflow_type === 'close') {
              return "";
        }
      },
      modalTitle: function() {
        if (this.workflow_type === 'forward_to_regions') {
            return "Forward to Regions";
        } else if (this.workflow_type === 'forward_to_wildlife_protection_branch') {
              return "Forward to Wildlife Protection Branch";
        } else if (this.workflow_type === 'allocate_for_follow_up') {
              return "Allocate for Follow Up";
        } else if (this.workflow_type === 'allocate_for_inspection') {
              return "Allocate for Inspection";
        } else if (this.workflow_type === 'allocate_for_case') {
              return "Allocate for Case";
        } else if (this.workflow_type === 'close') {
              return "Close Call/Email";
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
    filters: {
      formatDate: function(data) {
          return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
      }
    },
    methods: {
      ...mapActions('callemailStore', {
          saveCallEmail: 'saveCallEmail',
      }),
      ...mapActions({
          loadAllocatedGroup: 'loadAllocatedGroup',
      }),
      updateDistricts: function() {
        // this.district_id = null;
        this.availableDistricts = [];
        for (let record of this.regionDistricts) {
          if (this.region_id === record.id) {
            for (let district of record.districts) {
              for (let district_record of this.regionDistricts) {
                if (district_record.id === district) {
                  this.availableDistricts.push(district_record)
                }
              }
            }
          }
        }
        console.log(this.availableDistricts);
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
          console.log("updateAllocatedGroup");
          this.errorResponse = "";
          //this.allocatedGrouplength = 0;
          
          if (this.workflow_type === 'forward_to_wildlife_protection_branch') {
              for (let record of this.regionDistricts) {
                  if (record.district === 'KENSINGTON') {
                      this.district_id = null;
                      this.region_id = record.id;
                  }
              }
          }
          if (this.groupPermission && this.regionDistrictId) {
              let allocatedGroupResponse = await this.loadAllocatedGroup({
                  region_district_id: this.regionDistrictId, 
                  group_permission: this.groupPermission
              });
              if (allocatedGroupResponse.ok) {
                  console.log(allocatedGroupResponse.body.allocated_group);
                  //this.allocatedGroup = Object.assign({}, allocatedGroupResponse.body.allocated_group);
                  Vue.set(this, 'allocatedGroup', allocatedGroupResponse.body.allocated_group);
                  this.allocated_group_id = allocatedGroupResponse.body.group_id;
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
          }
      },

      ok: async function () {
          let is_valid_form = this.isValidForm();
          if (is_valid_form) {
              const response = await this.sendData();
              console.log(response);
              if (response === 'ok') {
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
              if (this.$v.assigned_to_id && this.$v.assigned_to_id.$invalid) {
                  this.errorResponse += 'Officer must be assigned\n';
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
          let vm = this;
          this.isModalOpen = false;
          let file_length = vm.files.length;
          this.files = [];
          for (var i = 0; i < file_length;i++){
              vm.$nextTick(() => {
                  $('.file-row-'+i).remove();
              });
          }
          this.attachAnother();
      },
      sendData: async function(){        
          let post_url = '/api/call_email/' + this.call_email.id + '/workflow_action/'
          let payload = new FormData(this.form);
          
          this.call_email.id ? payload.append('call_email_id', this.call_email.id) : null;
          this.workflowDetails ? payload.append('details', this.workflowDetails) : null;
          this.advice_details ? payload.append('advice_details', this.advice_details) : null;
          this.$refs.comms_log_file.commsLogId ? payload.append('call_email_comms_log_id', this.$refs.comms_log_file.commsLogId) : null;
          this.workflow_type ? payload.append('workflow_type', this.workflow_type) : null;
          this.modalTitle ? payload.append('email_subject', this.modalTitle) : null;
          this.referrersSelected ? payload.append('referrers_selected', this.referrersSelected) : null;
          this.district_id ? payload.append('district_id', this.district_id) : null;
          this.assigned_to_id ? payload.append('assigned_to_id', this.assigned_to_id) : null;
          this.inspection_type_id ? payload.append('inspection_type_id', this.inspection_type_id) : null;
          this.case_priority_id ? payload.append('case_priority_id', this.case_priority_id) : null;
          this.region_id ? payload.append('region_id', this.region_id) : null;
          this.allocated_group_id ? payload.append('allocated_group_id', this.allocated_group_id) : null;

          let callEmailRes = await this.saveCallEmail({ crud: 'save', 'internal': true });
          console.log(callEmailRes);
          if (callEmailRes.ok) {
              try {
                  let res = await Vue.http.post(post_url, payload);
                  if (res.ok) {    
                      this.$router.push({ name: 'internal-call-email-dash' });
                  }
              } catch(err) {
                  this.errorResponse = 'Error:' + err.statusText;
              } 
          } else {
              this.errorResponse = 'Error:' + callEmailRes.statusText;
          }
      },
      
      uploadFile(target,file_obj){
          let vm = this;
          let _file = null;
          var file_input = $('.'+target)[0];

          if (file_input.files && file_input.files[0]) {
              var reader = new FileReader();
              reader.readAsDataURL(file_input.files[0]); 
              reader.onload = function(e) {
                  _file = e.target.result;
              };
              _file = file_input.files[0];
          }
          file_obj.file = _file;
          file_obj.name = _file.name;
      },
      removeFile(index){
          let length = this.files.length;
          $('.file-row-'+index).remove();
          this.files.splice(index,1);
          this.$nextTick(() => {
              length == 1 ? this.attachAnother() : '';
          });
      },
      attachAnother(){
          this.files.push({
              'file': null,
              'name': ''
          })
      },
      addEventListeners: function() {
        let vm = this;
        // Initialise select2 for referrer
        $(document).ready(function() {
            //$(vm.$refs.referrerList).select2();
            $(vm.$refs.referrerList).select2({
                "theme": "bootstrap",
                allowClear: true,
                placeholder:"Select Referrer"
                        }).
            on("select2:select",function (e) {
                                const selected = $(e.currentTarget);
                                vm.referrersSelected = selected.val();
                           }).
            on("select2:unselect",function (e) {
                                const selected = $(e.currentTarget);
                                vm.referrersSelected = selected.val();
                            });
        });
      },
    },
    created: async function() {
        
        //await this.$parent.updateAssignedToId('blank');
        // regions
        let returned_regions = await cache_helper.getSetCacheList('Regions', '/api/region_district/get_regions/');
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
        // regionDistricts
        let returned_region_districts = await cache_helper.getSetCacheList(
            'RegionDistricts', 
            api_endpoints.region_district
            );
        Object.assign(this.regionDistricts, returned_region_districts);

        await this.updateAllocatedGroup();

        // referrers
        let returned_referrers = await cache_helper.getSetCacheList('CallEmail_Referrers', '/api/referrers.json');
        Object.assign(this.referrers, returned_referrers);
        // blank entry allows user to clear selection
        this.referrers.splice(0, 0, 
            {
              id: "", 
              name: "",
            });
        // add call_email vuex region_id and district_id to local component
        this.district_id = this.call_email.district_id;
        this.region_id = this.call_email.region_id;
        this.updateDistricts();
    },
    mounted: function() {
        this.form = document.forms.forwardForm;
        this.$nextTick(() => {
            this.addEventListeners();
        });
    }
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
