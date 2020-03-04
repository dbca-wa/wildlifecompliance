<template lang="html">
    <div id="LegalCaseWorkflow">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
          <div class="container-fluid">
            <div class="row">
            </div>

          </div>
            <div slot="footer">
                <div v-if="errorResponse" class="form-group">
                    <div class="row">
                        <div class="col-sm-12">
                            <strong>Error: {{ errorResponse }}</strong>
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

export default {
    name: "GenerateDocument",
    data: function() {
      return {
            officers: [],
            isModalOpen: false,
            processingDetails: false,
            form: null,
            workflowDetails: '',
            errorResponse: "",
            documentActionUrl: '',
            //allocatedGroup: [],
            allocated_group_id: null,
      }
    },
    components: {
      modal,
      filefield,
    },
    props:{
          document_type: {
              type: String,
              default: '',
          },
    },
    computed: {
      ...mapGetters('legalCaseStore', {
        legal_case: "legal_case",
      }),
      //allocatedGroupId: async function() {
      //    let allocated_group_id = null;
      //    if (this.workflow_type) {
      //        allocated_group_id = await this.updateAllocatedGroupId()
      //    }
      //    this.$nextTick(() => {
      //        return allocated_group_id;
      //    });
      //},
        /*
      regionDistrictId: function() {
          if (this.district_id || this.region_id) {
              return this.district_id ? this.district_id : this.region_id;
          } else {
              return null;
          }
      },
      */
      modalTitle: function() {
          let title = '';
          if (this.document_type === 'brief_of_evidence') {
              title = "Print Brief of Evidence";
          } else if (this.document_type === 'prosecution_brief') {
              title = "Print Prosecution Brief";
          }
          return title;
      },
        /*
      groupPermission: function() {
          if (this.workflow_type === 'send_to_manager') {
              return "manager";
          } else if (this.workflow_type === 'request_amendment') {
              return "officer";
          } else {
              return null;
          }
      },
      */
    },
    filters: {
      formatDate: function(data) {
          return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
      }
    },
    methods: {
      ...mapActions('legalCaseStore', {
          saveLegalCase: 'saveLegalCase',
          loadLegalCase: 'loadLegalCase',
          setLegalCase: 'setLegalCase',
      }),
        /*
      ...mapActions({
          loadAllocatedGroup: 'loadAllocatedGroup',
      }),
      updateAllocatedGroupId: async function() {
          console.log("updateAllocatedGroup");
          let allocated_group_id = null;
          this.errorResponse = "";
          if (this.regionDistrictId && this.groupPermission) {
              let allocatedGroupResponse = await this.loadAllocatedGroup({
              region_district_id: this.regionDistrictId,
              group_permission: this.groupPermission,
              });
              if (allocatedGroupResponse.ok) {
                  this.allocated_group_id = allocatedGroupResponse.body.group_id;
              } else {
                  // Display http error response on modal
                  this.errorResponse = allocatedGroupResponse.statusText;
              }
          } else {
              //this.allocatedGroup = [];
          }
      },
      */
      ok: async function () {
          const response = await this.sendData();
          console.log(response);
          if (response.ok) {
              this.close();
              //this.$router.push({ name: 'internal-legal-case-dash' });
          }
      },
      cancel: async function() {
          if (this.$refs.comms_log_file) {
              await this.$refs.comms_log_file.cancel();
          }
          this.isModalOpen = false;
          this.close();
      },
      close: function () {
          let vm = this;
          this.isModalOpen = false;
      },
      sendData: async function() {
          //let post_url = '/api/legal_case/' + this.legal_case.id + '/generate_brief_of_evidence_document/'
          let post_url = '/api/legal_case/' + this.legal_case.id + '/generate_document/'
          
          let payload = new FormData();
          payload.append('document_type', this.document_type);
          try {
              let res = await Vue.http.post(post_url, payload);
              // let res = await Vue.http.post(post_url);
              console.log(res);
              if (res.ok) {
                  return res
              }
          } catch(err) {
              this.errorResponse = err.statusText;
          }

      },
        /*
      createDocumentActionUrl: async function(done) {
        if (!this.legal_case.id) {
            // create inspection and update vuex
            let returned_legal_case = await this.saveLegalCase({ create: true, internal: true })
            await this.loadLegalCase({ legal_case_id: returned_legal_case.body.id});
        }
        // populate filefield document_action_url
        this.$refs.comms_log_file.document_action_url = this.legal_case.createInspectionProcessCommsLogsDocumentUrl;
        return done(true);
      },
      */

    },
    mounted: async function() {
        this.$nextTick(() => {
            /*
            console.log("update group id")
            this.updateAllocatedGroupId()
            */
        });
    },
    created: function() {
        /*
        if (this.legal_case && this.legal_case.id) {
            //this.inspection_type_id = this.inspection.inspection_type_id;
            //this.region_id = this.inspection.region_id;
            //this.district_id = this.inspection.district_id;
        }
        */

        // // ensure allocated group is current
        // await this.updateAllocatedGroup();
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