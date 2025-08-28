<template>
<div class="container" id="internalDash">
    <ReturnDashTable level="internal" :url="returns_url"/>
</div>
</template>
<script>
import ReturnDashTable from '@/components/common/returns_dashboard.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
    name: 'InternalReturnsDashboard',
    data() {
        let vm = this;
        return {
            returns_url: helpers.add_endpoint_join(api_endpoints.returns_paginated,'user_datatable_list/?format=datatables'),
        }

    },
    components: {
        ReturnDashTable,
    },
}
</script>
