<template id="application_conditions">
    <div>
        <template v-if="isFinalised || isPartiallyFinalised">
            <FormSection
                :form-collapse="false"
                label="Licence Details"
            >
                <div class="panel panel-default" >
                    <ul>
                        <li v-for="(activity, index) in finalisedActivities" v-bind:key="`licence_row_${index}`" :id="`licence_${activity.id}`">
                            <div v-if="activity.processing_status.id=='accepted'">
                                <b>{{activity.name}}:</b> Issued (valid for {{format(activity.start_date)}} - {{format(activity.expiry_date)}})
                            </div>
                            <div v-if="activity.processing_status.id=='declined'">
                                <b>{{activity.name}}:</b> Declined
                            </div>
                        </li>
                    </ul>
                </div>
            </FormSection>
        </template>
    </div>
</template>
<script>
import {
    api_endpoints,
    helpers
}
from '@/utils/hooks'
import datatable from '@vue-utils/datatable.vue'
import { mapGetters } from 'vuex'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'InternalApplicationLicenceDetails',
    components: {
        FormSection,
    },
    computed:{
        ...mapGetters([
            'application',
            'isPartiallyFinalised',
            'licenceActivities',
            'isFinalised',
        ]),
        finalisedActivities: function() {
            return this.licenceActivities(['accepted', 'declined']);
        },
    },
    methods: {
        format: function(activity_date) {
            return moment(activity_date).format('YYYY-MM-DD');
        },
    },
}
</script>
<style scoped>
</style>
