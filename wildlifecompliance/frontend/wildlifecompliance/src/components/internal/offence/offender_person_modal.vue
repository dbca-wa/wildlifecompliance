<template lang="html">
    <div>
        <modal transition="modal fade" @ok="ok()" @cancel="cancel()" :title="modalTitle" large force>
            <div class="container-fluid">
                <div class="row">
                    <div class="col-sm-12 form-group">
                      <div class="row">
                        <div class="col-sm-3">
                            <label class="control-label pull-left" for="offence-identifier">Test</label>
                        </div>
                        <div class="col-sm-6">
                            <div v-if="offender">
                                <input type="text" class="form-control" name="identifier" placeholder="" v-model="offender.test" v-bind:key="offender.id">
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
                                <span style="white-space: pre;" v-html="errorResponse"></span>
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
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
import "bootstrap/dist/css/bootstrap.css";

export default {
  name: "Offender",
  data: function() {
    let vm = this;
    return {
      uuid: 0,
    }
  },
  props:{
    offender: {
      requird: true,
    }
  },
  computed: {
    modalTitle: function() {
      return "Update Offender";
    },
  },
  methods: {
    sendData: async function() {
        let vm = this;
        let res //= await TODO
        return res
    },
    ok: async function() {
        try {
            this.processingDetails = true;
            let response = await this.sendData();

            if (response.ok) {
                // Refresh offence table TODO
            }
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
        //await swal("Error", errorText, "error");
    },
    cancel: function() {
        this.processingDetails = false;
        this.close();
    },
    close: function() {
        this.processingDetails = false;
        this.isModalOpen = false;
    },
  }  
};
</script>