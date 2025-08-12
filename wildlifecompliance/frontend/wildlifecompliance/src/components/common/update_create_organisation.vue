<template>
    <div class="container-fluid" id="internalOrgInfo">
       <div class="row">
            <div class="col-sm-12">
                <FormSection
                :form-collapse="false"
                label="Organisation Details"
                index="org_details"
                >
                    <div class="panel panel-default">
                      <div class="form-horizontal">
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Name</label>
                            <div class="col-sm-6">
                                <input type="text" class="form-control" name="first_name" placeholder="" v-model="organisation.name">
                            </div>
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label" >ABN</label>
                            <div class="col-sm-6">
                                <input type="text" class="form-control" name="last_name" placeholder="" v-model="organisation.abn">
                            </div>
                          </div>
                       </div>
                    </div>
                </FormSection>
            </div>
       </div>
       <div class="row">
            <div class="col-sm-12">
                <FormSection
                :form-collapse="false"
                label="Address Details"
                index="address_details"
                >
                    <div class="panel panel-default">
                      <div class="form-horizontal">
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label">Street</label>
                            <div class="col-sm-6">
                                <input type="text" class="form-control" name="street" placeholder="" v-model="organisation.address.line1">
                            </div>
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label" >Town/Suburb</label>
                            <div class="col-sm-6">
                                <input type="text" class="form-control" name="surburb" placeholder="" v-model="organisation.address.locality">
                            </div>
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label">State</label>
                            <div class="col-sm-2">
                                <input type="text" class="form-control" name="country" placeholder="" v-model="organisation.address.state">
                            </div>
                            <label for="" class="col-sm-2 control-label">Postcode</label>
                            <div class="col-sm-2">
                                <input type="text" class="form-control" name="postcode" placeholder="" v-model="organisation.address.postcode">
                            </div>
                          </div>
                          <div class="form-group">
                            <label for="" class="col-sm-3 control-label" >Country</label>
                            <div class="col-sm-4">
                                <select class="form-control" name="country" v-model="organisation.address.country">
                                    <option v-for="c in countries" :value="c.code">{{ c.name }}</option>
                                </select>
                            </div>
                          </div>
                       </div>
                  </div>
                </FormSection>
            </div>
        </div>
        <div class="form-group">
            <div class="col-sm-12">
                <div v-if="show_spinner"><i class='fa fa-2x fa-spinner fa-spin pull-right'></i></div>
                <div v-else>
                    <button class="pull-right btn btn-primary" @click.prevent="save()">Save Organisation</button>
                </div>
            </div>
        </div>
   </div> 
</template>

<script>
import Vue from 'vue'
import { api_endpoints, helpers, cache_helper, fetch_util } from '@/utils/hooks'
import datatable from '@vue-utils/datatable.vue'
import AddContact from '@common-components/add_contact.vue'
import utils from '../internal/utils'
import api from '../internal/api'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'Organisation',
    data () {
        let vm = this;
        return {
            adBody: 'adBody'+vm._uid,
            aBody: 'aBody'+vm._uid,
            pdBody: 'pdBody'+vm._uid,
            pBody: 'pBody'+vm._uid,
            cdBody: 'cdBody'+vm._uid,
            cBody: 'cBody'+vm._uid,
            oBody: 'oBody'+vm._uid,
            dTab: 'dTab'+vm._uid,
            oTab: 'oTab'+vm._uid,
            idBody: 'idBody'+vm._uid,
            organisation: {
                address: {}
            },
            myorgperms: null,
            show_spinner: false,
            countries: [],
        }
    },
    components: {
        datatable,
        FormSection
    },
    created: async function() {
        // Populate country drop-down list
        let returned_country_list = await cache_helper.getSetCacheList(
          'Countries',
          api.countries
          );
        Object.assign(this.countries, returned_country_list);
        // Set selected country to Australia
        this.organisation.address.country = 'AU';
    },
    methods: {
        save: async function() {
            this.show_spinner = true;
            let post_url = '/api/organisations_compliancemanagement/';
            
            let returnedOrganisation = await fetch.fetchUrl(post_url, {method:'POST', body:JSON.stringify(this.organisation)});
            console.log(returnedOrganisation)
            this.show_spinner = false;
        },
    }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.top-buffer-s {
    margin-top: 10px;
}
.actionBtn {
    cursor: pointer;
}
.hidePopover {
    display: none;
}
</style>
