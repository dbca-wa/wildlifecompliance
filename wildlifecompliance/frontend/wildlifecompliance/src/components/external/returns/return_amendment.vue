<template>
    <div v-if="isReturnsLoaded">
        <div v-if="visibleRequests.length" class="row" style="color:red;">
            <div class="col-lg-12 float-end">
                <FormSection
                    :form-collapse="false"
                    label="An amendment has been requested for this Return"
                >
                    <div class="panel panel-default">
                        <div v-for="(a, a_idx) in visibleRequests" v-bind:key="`ret_amend_${a_idx}`">
                            <p v-if="a.text"><b>Details:</b>
                                <div v-for="(t, t_idx) in splitText(a.text)" v-bind:key="`ret_text_${t_idx}`">{{t}}<br></div>
                            </p> 
                        </div>
                    </div>
                </FormSection>
            </div>
        </div>
    </div>
</template>


<script>
import { v4 as uuid } from 'uuid';
import Vue from 'vue'
import { mapActions, mapGetters } from 'vuex'
import helpers from "@/utils/helpers.js";

import FormSection from "@/components/forms/section_toggle.vue";
export default {
  name:'returns-amendment-details',
  data: function() {
    let vm = this;
    return {
        returnsAmendBody: 'returnsAmendBody'+uuid(),
    }
  },
  components: {
    FormSection,
  },
  computed: {
    ...mapGetters([
        'isReturnsLoaded',
        'returns',
    ]),
    isVisible: function() {
        return true;
    },
    visibleRequests: function() {
        return this.returns.amendment_requests;
    }
  },
  methods: {
    splitText: helpers.splitText
  },
}
</script>
