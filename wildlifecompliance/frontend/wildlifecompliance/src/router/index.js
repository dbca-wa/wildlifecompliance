import Vue from 'vue'
import { createRouter, createWebHistory } from 'vue-router';
import Organisations from '@/components/user/manage_organisations.vue'
import ManageOrganisation from '@/components/external/organisations/manage.vue'
import external_routes from '@/components/external/routes'
import internal_routes from '@/components/internal/routes'
import { api_endpoints, fetch_util } from "@/utils/hooks";

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
    const res = await fetch_util.fetchUrl(api_endpoints.is_compliance_management_callemail_readonly_user);
    const isComplianceManagementCallemailReadonlyUser = res.compliance_management_callemail_readonly_user;
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