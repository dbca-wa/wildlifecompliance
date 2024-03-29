<template lang="html">
    <div id="RunningSheetHistory">
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
          <div class="container-fluid">
            <div class="row">
                <div class="col-sm-12 form-group"><div class="row">
                    <div>
                        <datatable 
                        ref="running_sheet_hist_instance" 
                        id="running-sheet-hist-instance" 
                        :dtOptions="dtOptionsRunningSheetHistory" 
                        :dtHeaders="dtHeadersRunningSheetHistory"
                        parentStyle=" "
                        />
                    </div>
                </div></div>
              
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
import { required, minLength, between } from 'vuelidate/lib/validators'
import datatable from '@vue-utils/datatable.vue'

export default {
    name: "RunningSheetHistory",
    data: function() {
      return {
            isModalOpen: false,
            processingDetails: false,
            errorResponse: "",
            runningSheetHist: [],
            dtHeadersRunningSheetHistory: [
                "date_modified",
                "Date",
                "Time",
                "User",
                "Description",
                "deleted",
            ],
            dtOptionsRunningSheetHistory: {
                order: [
                    [1, 'desc']
                ],

                columns: [
                    {
                        data: 'id',
                        visible: false,
                        mRender: function(data, type, row) {
                            return row.date_modified;
                        }
                    },
                    {
                        data: 'id',
                        mRender: function(data, type, row) {
                            let retStr = row.date_mod;
                            return retStr;
                        }
                    },
                    {
                        data: 'id',
                        mRender: function(data, type, row) {
                            let retStr = row.time_mod;
                            return retStr;
                        }
                    },
                    {
                        data: 'id',
                        mRender: function(data, type, row) {
                            let retStr = row.user_full_name;
                            return retStr;
                        }
                    },
                    {
                        data: 'id',
                        mRender: function(data, type, row) {
                            let retStr = '';
                            retStr = `<div id=${row.number} style="min-height:20px" contenteditable="false">${row.description}</div>`
                            if (row.deleted) {
                                retStr = '<strike>' + retStr + '</strike>';
                            }
                            return retStr;

                        }
                    },
                    {
                        data: 'id',
                        visible: false,
                        mRender: function(data, type, row) {
                            return row.deleted;
                        }
                    },

                ]
            }
      }
    },
    components: {
      modal,
      datatable,
    },
    computed: {
      ...mapGetters('legalCaseStore', {
        legal_case: "legal_case",
      }),
      modalTitle: function() {
          return "Running Sheet History - " + this.runningSheetHistoryEntryInstance
      },
    },
    props: {
        runningSheetHistoryEntryInstance: {
            required: true,
        },
    },
    filters: {
      formatDate: function(data) {
          return data ? moment(data).format("DD/MM/YYYY HH:mm:ss") : "";
      }
    },
    methods: {
        tokenToHtml: function(description) {
            let parsedText = description;
            // Person transform
            const personTokenRegex = /\{\{ \"person\_id\"\: \"\d+\"\, \"full\_name\"\: \"\w+(\s\w+)*\" \}\}/g;
            const personIdRegex = /\{\{ \"person\_id\"\: \"\d+/g;
            // const personNameRegex = /\"full\_name\"\: \"\w+ \w+/g;
            const personNameRegex = /\"full\_name\"\: \"\w+(\s\w+)*/g;
            let personTokenArray = [...description.matchAll(personTokenRegex)];
            for (let personToken of personTokenArray) {
                let personIdArray = [...personToken[0].matchAll(personIdRegex)];
                let personIdStr = personIdArray[0][0]
                let personId = personIdStr.substring(17)
                let nameArray = [...personToken[0].matchAll(personNameRegex)];
                if (nameArray && nameArray.length > 0) {
                    let nameStr = nameArray[0][0]
                    let fullName = nameStr.substring(14)
                    parsedText = parsedText.replace(
                        personToken[0],
                        //`<a contenteditable="false" target="_blank" href="/internal/users/${id}">${fullName}</a>`
                        `<span contenteditable="false" id="individual-${personId}" class="entity_edit">${fullName}</span>`
                    );
                }
            }
            // Artifact transform
            //const artifactTokenRegex = /\{\{ \"artifact\_id\"\: \"\d+\"\, \"identifier\"\: \"\w+(\s\w+)*\" \}\}/g;
            const artifactTokenRegex = /\{\{ \"\w+\_artifact\_id\"\: \"\d+\"\, \"identifier\"\: \"\w+(\s\w+)*\" \}\}/g;
            const artifactIdRegex = /\w+\_artifact\_id\"\: \"\d+/g;
            //const artifactIdRegex = /artifact\_id\"\: \"\d+/g;
            const artifactIdentifierRegex = /\"identifier\"\: \"\w+(\s\w+)*/g
            let artifactTokenArray = [...description.matchAll(artifactTokenRegex)];
            for (let artifactToken of artifactTokenArray) {
                let artifactIdArray = [...artifactToken[0].matchAll(artifactIdRegex)];
                let artifactIdStr = artifactIdArray[0][0]
                let artifactType = artifactIdStr.split("_")[0] + "_artifact";
                let artifactIdStrTrunc = artifactIdStr.split("_")[2];
                let artifactId = artifactIdStrTrunc.substring(6)
                let identifierArray = [...artifactToken[0].matchAll(artifactIdentifierRegex)];
                if (identifierArray && identifierArray.length > 0) {
                    let identifierStr = identifierArray[0][0]
                    let identifier = identifierStr.substr(15)
                    let elemId = artifactType + "-" + artifactId;
                    parsedText = parsedText.replace(
                        artifactToken[0],
                        `<span contenteditable="false" id="${elemId}" class="entity_edit">${identifier}</span>`
                        );
                }
            }
            return parsedText
        },
        /*

        tokenToUrl: function(description) {
            console.log("tokenToUrl")
            let parsedText = description;
            const personTokenRegex = /\{\{ \"person\_id\"\: \"\d+\"\, \"full\_name\"\: \"\w+(\s\w+)*\" \}\}/g;
            const personIdRegex = /\{\{ \"person\_id\"\: \"\d+/g;
            const personNameRegex = /\"full\_name\"\: \"\w+ \w+/g;
            let personTokenArray = [...description.matchAll(personTokenRegex)];
            for (let personToken of personTokenArray) {
                console.log(personToken)
                let idArray = [...personToken[0].matchAll(personIdRegex)];
                console.log(idArray)
                let idStr = idArray[0][0]
                let id = idStr.substring(17)
                console.log(id)
                let nameArray = [...personToken[0].matchAll(personNameRegex)];
                console.log(nameArray)
                let nameStr = nameArray[0][0]
                let fullName = nameStr.substring(14)
                console.log(id)
                parsedText = parsedText.replace(
                    personToken[0],
                    `<a contenteditable="false" target="_blank" href="/internal/users/${id}">${fullName}</a>`
                );
                console.log(parsedText)
            }
            return parsedText
        },
        */
        constructRunningSheetTable: function(){
            console.log("constructInstanceRunningSheetTable")
            this.$refs.running_sheet_hist_instance.vmDataTable.clear().draw();
            let actionColumn = !this.readonlyForm;
            if (this.runningSheetHist){
                for(let i = 0;i < this.runningSheetHist.length; i++){
                    this.$refs.running_sheet_hist_instance.vmDataTable.row.add({ 
                        "id": this.runningSheetHist[i].id,
                        "number": this.runningSheetHist[i].number,
                        "date_modified": this.runningSheetHist[i].date_modified,
                        "date_mod": this.runningSheetHist[i].date_mod,
                        "time_mod": this.runningSheetHist[i].time_mod,
                        "user_full_name": this.runningSheetHist[i].user_full_name,
                        "description": this.runningSheetHist[i].description,
                        "deleted": this.runningSheetHist[i].deleted,
                        "action": actionColumn,
                    }).draw();
                }
            }
            console.log("constructRunningSheetTable - end")
        },
        ok: async function () {
          this.close();
        },
        cancel: function() {
          this.isModalOpen = false;
          this.close();
        },
        close: function () {
          this.isModalOpen = false;
        },
    },
    created: async function() {
        let fetchUrl = helpers.add_endpoint_join(
            api_endpoints.legal_case,
            this.legal_case.id + "/running_sheet_history/"
            )
        let returnedRunningSheetHist = await Vue.http.post(
            fetchUrl, 
            { "running_sheet_entry_number": this.runningSheetHistoryEntryInstance }
        );
        if (returnedRunningSheetHist && returnedRunningSheetHist.body) {
            for (let v of returnedRunningSheetHist.body.versions) {
                let entryVersion = _.cloneDeep(v.entry_fields);
                //entryVersion.description = this.tokenToUrl(entryVersion.description)
                entryVersion.description = this.tokenToHtml(entryVersion.description)
                this.runningSheetHist.push(entryVersion);
            }
        }
        /*
        for (let r of this.legal_case.running_sheet_entries) {
          if (r.number === this.runningSheetHistoryEntryInstance && r.versions && r.versions.length > 0) {
              for (let rr of r.versions) {
                  let entryVersion = _.cloneDeep(rr.entry_fields);
                  entryVersion.description = this.tokenToUrl(entryVersion.description)
                  this.runningSheetHist.push(entryVersion);
              }
          }
        }
        */
        this.$nextTick(() => {
            this.constructRunningSheetTable();
        });
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
