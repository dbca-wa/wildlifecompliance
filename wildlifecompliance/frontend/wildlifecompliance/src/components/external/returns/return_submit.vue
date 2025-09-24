<template>
    <FormSection
        :form-collapse="false"
        label="Return"
    >
        <div class="panel panel-default">
            <div v-if="isReturnsLoaded" class="col-sm-offset-3 col-sm-6 borderDecoration">
                <strong>Your Return has been submitted successfully.</strong>
                <br/>
                <table>
                    <thead>
                    <tr>
                        <td><strong>Reference number:&nbsp;</strong></td>
                        <td><strong>{{returns.lodgement_number}}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Lodgement date:</strong></td>
                        <td><strong> {{ formatDate(returns.lodgement_date) }}</strong></td>
                    </tr>
                    <tr>
                        <td><strong>Invoice:</strong></td>
                        <td><a :href="returns.invoice_url" target="_blank"><i style="color:red" class="bi bi-file-pdf"></i></a></td>
                    </tr>
                    </thead>
                </table>
                <a href="/" style="margin-top:15px;" class="btn btn-primary">Back to dashboard</a>
            </div>
            <div v-else class="col-sm-offset-3 col-sm-6 borderDecoration">
                <strong>Sorry it looks like there isn't any details currently in your session.</strong>
                <br /><a href="/" style="margin-top:15px;" class="btn btn-primary">Back to dashboard</a>
            </div>
        </div>
        <input type='hidden' name="table_name" :value="returns.table[0].name" />
    </FormSection>
</template>

<script>
import { v4 as uuid } from 'uuid';
import { mapActions, mapGetters } from 'vuex'
import CommsLogs from '@common-components/comms_logs.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
  name: 'ReturnConfirmation',
  data() {
    let vm = this;
    return {
      pdBody: 'pdBody' + uuid(),
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
