import Vue from 'vue'
import Router from 'vue-router'
import MyUserDetails from '@/components/user/manage_my_user_details.vue'
import Organisations from '@/components/user/manage_organisations.vue'
import ManageOrganisation from '@/components/external/organisations/manage.vue'
import ProfileDashTable from '@/components/user/profile_dashboard.vue'
import CreateProfile from '@/components/user/profile_create.vue'
import EditProfile from '@/components/user/profile_manage.vue'
import external_routes from '@/components/external/routes'
import internal_routes from '@/components/internal/routes'
import { api_endpoints, helpers, cache_helper } from "@/utils/hooks";
Vue.use(Router)

const router = new Router({
    mode: 'history',
    routes: [
        {
          path: '/firsttime',
          name: 'first-time',
          component: MyUserDetails
        },
        {
          path: '/account',
          name: 'account',
          component: MyUserDetails
        },
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
    //if (to.name !=="internal-call-email-dash" && isComplianceManagementCallemailReadonlyUser) next({name:"internal-call-email-dash"})
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
export { router as default }
