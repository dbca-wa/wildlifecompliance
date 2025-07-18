import Vue from 'vue'
import { createRouter, createWebHistory } from 'vue-router';
import Organisations from '@/components/user/manage_organisations.vue'
import ManageOrganisation from '@/components/external/organisations/manage.vue'
import ProfileDashTable from '@/components/user/profile_dashboard.vue'
import CreateProfile from '@/components/user/profile_create.vue'
import EditProfile from '@/components/user/profile_manage.vue'
import external_routes from '@/components/external/routes'
import internal_routes from '@/components/internal/routes'
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";

const router = new createRouter({
    history: createWebHistory(),
    strict: false,
    routes: [
        {
          path: '/ledger-ui/accounts',
          name: 'organisation',
          component: Organisations
        },
        {
          path: '/ledger-ui/organisation/:org_id',
          name: 'manage_organisation',
          component: ManageOrganisation
        },
        external_routes,
        internal_routes
    ]
});
router.beforeEach(async (to, from, next) => {
    const res = await Vue.http.get(api_endpoints.is_compliance_management_callemail_readonly_user);
    const isComplianceManagementCallemailReadonlyUser = res.body.compliance_management_callemail_readonly_user;
    if (!([
        "first-time",
        "account",
        "organisation",
        "manage_organisation",
        "internal-call-email-dash",
        "view-call-email"].includes(to.name)) && isComplianceManagementCallemailReadonlyUser) {
        // Call Email Read Only users can only access these four routes
        next({name:"internal-call-email-dash"})
    }
    else next()
});

export default router;