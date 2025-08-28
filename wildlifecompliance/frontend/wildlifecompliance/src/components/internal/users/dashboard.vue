<template>
<div class="container" id="internalDash">
    <UserDashTable level="internal" :url="users_url"/>
</div>
</template>
<script>
import UserDashTable from '@/components/common/users_dashboard.vue'
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
export default {
    name: 'InternalUserDashboard',
    data() {
        let vm = this;
        return {
            users_url: api_endpoints.users,
        }
    
    },
    components: {
        UserDashTable,
    },
}
</script>
