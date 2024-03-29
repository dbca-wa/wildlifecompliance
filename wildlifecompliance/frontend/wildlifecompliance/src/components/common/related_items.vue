<template>
    <div>
        <div class="col-sm-12 form-group"><div class="row">
            <div class="col-sm-12">
                <datatable parentStyle=" " ref="related_items_table" id="related-items-table" :dtOptions="dtOptionsRelatedItems" :dtHeaders="dtHeadersRelatedItems" />
            </div>
        </div></div>
        <div class="col-sm-12 form-group"><div class="row">
            <div class="col-sm-12">
            <!--WeakLinks @weak-link-selected="createWeakLink"/-->
                <WeakLinks ref="weak_links_lookup" :readonlyForm="readonlyForm" :displayedEntityType="displayedEntityType" :displayedEntityId="displayedEntityId"/>
            </div>
        </div></div>
    </div>
</template>
<script>
import Vue from "vue";
import datatable from '@vue-utils/datatable.vue'
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import utils from "@/components/external/utils";
import { mapState, mapGetters, mapActions, mapMutations } from "vuex";
import moment from 'moment';
import 'bootstrap/dist/css/bootstrap.css';
import 'eonasdan-bootstrap-datetimepicker';
require("select2/dist/css/select2.min.css");
require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");
import WeakLinks from '@/components/common/weak_links.vue';

export default {
    name: "RelatedItems",
    props: {
          parent_update_related_items: {
              type: Function,
          },
          readonlyForm: {
              type: Boolean,
              default: false,
          },
          parentComponentName: {
              type: String,
          },
    },

    data: function() {
    return {
      displayedEntityType: null,
      dtHeadersRelatedItems: [
          'Number',
          'Type',
          'Description',
          'Comment',
          'Action',
      ],
      dtOptionsRelatedItems: {
          columns: [
              {
                  data: 'identifier',
              },
              {
                  data: 'model_name',
              },
              {
                  data: 'descriptor',
              },
              {
                  data: 'AllFields',
                  mRender: function(data, type, row){
                      let comment = ''
                      if (row.AllFields.weak_link) {
                          comment = row.AllFields.comment;
                      }
                      return comment;
                  }
              },
              {
                  data: 'AllFields',
                  mRender: function(data, type, row){
                      let links = '';
                      if (row.AllFields.weak_link && row.AllFields.can_user_action) {
                          links += '<a href="#" class="remove_button" second-content-type="' + row.AllFields.second_content_type + '" second-object-id="' + row.AllFields.second_object_id + '">Remove</a><br>';
                      }
                      links += row.AllFields.action_url;
                      return links
                  }
              },
          ]
      },
    };
  },
  components: {
    datatable,
    WeakLinks,
  },
  watch: {
      displayedEntityRelatedItems: {
          handler: function (){
              this.$nextTick(() => {
                  this.constructRelatedItemsTable();
              });
          },
          deep: true
      },
  },
  computed: {
    ...mapGetters('documentArtifactStore', {
      document_artifact: "document_artifact",
    }),
    ...mapGetters('physicalArtifactStore', {
      physical_artifact: "physical_artifact",
    }),
    ...mapGetters('callemailStore', {
      call_email: "call_email",
    }),
    ...mapGetters('inspectionStore', {
      inspection: "inspection",
    }),
    ...mapGetters('offenceStore', {
      offence: "offence",
    }),
    ...mapGetters('sanctionOutcomeStore', {
      sanction_outcome: "sanction_outcome",
    }),
    ...mapGetters('legalCaseStore', {
      legal_case: "legal_case",
    }),
    csrf_token: function() {
      return helpers.getCookie("csrftoken");
    },
    displayedEntity: function() {
        let displayed_entity = null;
        if (this.call_email && this.call_email.id) {
            this.displayedEntityType = 'callemail';
            displayed_entity = this.call_email;
        } else if (this.inspection && this.inspection.id) {
            this.displayedEntityType = 'inspection';
            displayed_entity = this.inspection;
        } else if (this.offence && this.offence.id) {
            this.displayedEntityType = 'offence';
            displayed_entity = this.offence;
        } else if (this.sanction_outcome && this.sanction_outcome.id) {
            this.displayedEntityType = 'sanctionoutcome';
            displayed_entity = this.sanction_outcome;
        } else if (this.legal_case && this.legal_case.id && this.parentComponentName === 'legal_case') {
            this.displayedEntityType = 'legalcase';
            displayed_entity = this.legal_case;
        } else if (this.physical_artifact && this.physical_artifact.id && this.parentComponentName === 'physical_artifact') {
            this.displayedEntityType = 'physicalartifact';
            displayed_entity = this.physical_artifact;
        } else if (this.document_artifact && this.document_artifact.id && this.parentComponentName === 'document_artifact') {
            this.displayedEntityType = 'documentartifact';
            displayed_entity = this.document_artifact;
        }
        return displayed_entity;
    },
    displayedEntityId: function() {
        let retVal = null;
        if (this.displayedEntity) {
            retVal = this.displayedEntity.id;
        }
        return retVal
    },
    displayedEntityRelatedItems: function() {
        let retVal = null;
        if (this.displayedEntity && this.displayedEntity.related_items) {
            retVal = this.displayedEntity.related_items;
        }
        return retVal
    },

  },
  methods: {
    createWeakLink: async function() {
        let url = '/api/create_weak_link/'
        let payload = {
            'can_user_action': this.displayedEntity.can_user_action,
            'first_content_type': this.displayedEntityType,
            'first_object_id': this.displayedEntity.id,
            'second_content_type': this.$refs.weak_links_lookup.second_content_type,
            'second_object_id': this.$refs.weak_links_lookup.second_object_id,
            'comment': this.$refs.weak_links_lookup.comment,
        }
        // post payload to url, then
        let relatedItems = await Vue.http.post(url, payload);
        if (relatedItems.ok) {
            await this.parent_update_related_items(relatedItems.body);
            return relatedItems
        }

    },
    removeWeakLink: async function(e) {
        let secondContentType = e.target.getAttribute("second-content-type");
        let secondObjectId = e.target.getAttribute("second-object-id");
        let url = '/api/remove_weak_link/'
        let payload = {
            'can_user_action': this.displayedEntity.can_user_action,
            'first_content_type': this.displayedEntityType,
            'first_object_id': this.displayedEntity.id,
            'second_content_type': secondContentType,
            'second_object_id': secondObjectId,
        }
        // post payload to url, then
        let relatedItems = await Vue.http.post(url, payload);
        if (relatedItems.ok) {
            await this.parent_update_related_items(relatedItems.body);
        }
    },

    constructRelatedItemsTable: function() {
        this.$refs.related_items_table.vmDataTable.clear().draw();

        if(this.displayedEntity && this.displayedEntity.related_items){
          for(let i = 0; i< this.displayedEntity.related_items.length; i++){
            //let already_exists = this.$refs.related_items_table.vmDataTable.columns(0).data()[0].includes(this.displayedEntity.related_items[i].id);

            let allfieldsColumn = new Object();
            Object.assign(allfieldsColumn, this.displayedEntity.related_items[i]);
            allfieldsColumn.can_user_action = this.displayedEntity.can_user_action;

            //if (!already_exists) {
            this.$refs.related_items_table.vmDataTable.row.add(
                {
                    'identifier': this.displayedEntity.related_items[i].identifier,
                    'descriptor': this.displayedEntity.related_items[i].descriptor,
                    'model_name': this.displayedEntity.related_items[i].model_name,
                    'AllFields': allfieldsColumn,
                }
            ).draw();
            //}
          }
        }
    },
    addEventListeners: function() {
      $('#related-items-table').on(
          'click',
          '.remove_button',
          this.removeWeakLink,
          );
    }
  },
  created: async function() {
  },
  mounted: function() {
      this.$nextTick(() => {
          this.addEventListeners();
          this.constructRelatedItemsTable();

      });
  }
};
</script>

<style lang="css">
#main-column {
  padding-left: 2%;
  padding-right: 0;
  margin-bottom: 50px;
}
.awesomplete {
    width: 100% !important;
}
.nav>li>a:focus, .nav>li>a:hover {
  text-decoration: none;
  background-color: #eee;
}
.nav-item {
  background-color: hsla(0, 0%, 78%, .8) !important;
  margin-bottom: 2px;
}
.advice-url-label {
  visibility: hidden;
}
.advice-url {
  padding-left: 20%;
}
.action-button {
    margin-top: 5px;
}
</style>
