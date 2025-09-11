<template lang="html">
    <div v-if="isApplicationLoaded && !application_readonly && isVisible">
        <div v-if="visibleRequests.length" class="row" style="color:red;">
            <div class="col-lg-12 float-end">
                <FormSection
                    :form-collapse="false"
                    label="An amendment has been requested for this Application"
                >
                <div class="panel panel-default">
                    <div v-for="a in visibleRequests">
                        <p><b>Activity:</b> {{a.licence_activity.name}}</p>
                        <p><b>Reason:</b> {{a.reason.name}}</p>
                        <p v-if="a.text"><b>Details:</b>
                            <div v-for="t in splitText(a.text)">{{t}}<br></div></p> 
                    </div>
                </div>
                </FormSection>
            </div>
        </div>
    </div>
</template>


<script>
import Vue from 'vue'
import { mapActions, mapGetters } from 'vuex'
import helpers from "@/utils/helpers.js";

import FormSection from "@/components/forms/section_toggle.vue";
export default {
  name:'amendment-request-details',
  data: function() {
    return {
    }
  },
  props:{
      activity_id: {
          type: Number,
          required: true
      }
  },
  components: {
    FormSection,
  },
  computed: {
    ...mapGetters([
        'application_readonly',
        'amendment_requests',
        'selected_activity_tab_id',
        'isApplicationLoaded',
    ]),
    isVisible: function() {
        return this.activity_id == this.selected_activity_tab_id;
    },
    visibleRequests: function() {
        return this.amendment_requests.filter(request => request.licence_activity.id == this.activity_id);
    }
  },
  methods: {
    splitText: helpers.splitText
  },
}
</script>
