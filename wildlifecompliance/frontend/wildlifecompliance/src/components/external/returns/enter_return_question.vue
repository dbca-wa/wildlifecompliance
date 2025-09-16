<template>
    <FormSection
        :form-collapse="false"
        label="Return"
    >
      <div class="panel panel-default">
            <div class="col-sm-16">
                <div>
                    <AmendmentRequestDetails v-show="is_external"/>
                    <div v-for="item in returns.table" v-bind:key="`headers_${item.headers}`">
                        <renderer-block v-for="(question,key) in item.headers"
                              :component="question"
                              v-bind:key="`q_${key}`"
                        />
                    </div>
                </div>
                <!-- End of Question Return -->
            </div>
        </div>
        <input type='hidden' name="table_name" :value="returns.table[0].name" />
    </FormSection>
</template>

<script>
import { v4 as uuid } from 'uuid';
 'vue'
import { mapActions, mapGetters } from 'vuex'
import CommsLogs from '@common-components/comms_logs.vue'
import AmendmentRequestDetails from './return_amendment.vue';
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
  name: 'externalReturnQuestion',
  data() {
    let vm = this;
    return {
      pdBody: 'pdBody' + uuid(),
    }
  },
  computed: {
    ...mapGetters([
        'isReturnsLoaded',
        'returns',
        'is_external',
    ]),
  },
  components: {
    FormSection,
    AmendmentRequestDetails,
  },
  methods: {
    ...mapActions({
      load: 'loadReturns',
    }),
    ...mapActions([
        'setReturns',
    ]),
  },
}
</script>
