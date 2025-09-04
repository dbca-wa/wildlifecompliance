import 'vite/modulepreload-polyfill';

// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue';
// window._ = _;
import $ from 'jquery';
window.$ = $
window.jQuery = $
//import 'jquery-ui';
import 'jquery-validation';
import select2 from 'select2';
select2()
import swal from 'sweetalert2';
window.swal = swal;
import _ from 'lodash'
window._ = _
import { createApp } from 'vue';
import App from '@/App.vue';
import router from '@/router';
import helpers from '@/utils/helpers';
import store from '@/store';
import RendererBlock from '@/components/common/renderer_block.vue';
import ComplianceRendererBlock from '@/components/common/compliance_renderer_block.vue';
import { useVuelidate } from '@vuelidate/core'

import { extendMoment } from 'moment-range';
 
import 'datatables.net-bs5';
import 'datatables.net-buttons-bs5';
import 'datatables.net-responsive-bs5';
import 'datatables.net-buttons/js/dataTables.buttons.js';

import jsZip from 'jszip';
window.JSZip = jsZip;

import 'select2';
import "sweetalert2/dist/sweetalert2.css";

import 'select2/dist/css/select2.min.css';
import 'select2-bootstrap-5-theme/dist/select2-bootstrap-5-theme.min.css';
import '@/../node_modules/datatables.net-bs5/css/dataTables.bootstrap5.min.css';
import '@/../node_modules/datatables.net-responsive-bs5/css/responsive.bootstrap5.min.css';
import '@/../node_modules/@fortawesome/fontawesome-free/css/all.min.css';

//import 'summernote/dist/summernote';
import 'summernote/dist/summernote-lite.min.css';
import 'summernote/dist/summernote-lite.min.js';

import '@/../node_modules/@fortawesome/fontawesome-free/css/all.min.css';
import '@/../node_modules/datatables.net-bs5/css/dataTables.bootstrap5.min.css';

extendMoment(moment);

//Vue.config.devtools = true;
Vue.config.productionTip = false

export default {
  setup () {
    return { v$: useVuelidate() }
  },
}

Vue.component('renderer-block', RendererBlock);
Vue.component('compliance-renderer-block', ComplianceRendererBlock);

// Add CSRF Token to every request
const customHeaders = new Headers({
    'X-CSRFToken': helpers.getCookie('csrftoken'),
});
const customHeadersJSON = new Headers({
    'X-CSRFToken': helpers.getCookie('csrftoken'),
    'Content-Type': 'application/json',
});

var mapbox_access_token = '';

Vue.mixin({
    methods: {
        retrieveMapboxAccessToken: async function(){
            let ret_val = await $.ajax('/api/geocoding_address_search_token');
            return ret_val;
        },
        toCurrency: function(value) {
            if (typeof value !== "number") {
                return value;
            }
            var formatter = new Intl.NumberFormat('en-AU', {
                style: 'currency',
                currency: 'AUD',
                minimumFractionDigits: 2
            });
            return formatter.format(value);
        },
        formatDate: function(data) {
            return data ? moment(data).format('YYYY-MM-DD'): '';
        }
    },
})

const app = createApp(App);
app.use(store)
app.use(router);
router.isReady().then(() => app.mount('#app'));

const fetch = window.fetch;
window.fetch = ((originalFetch) => {
    return async (...args) => {
        if (args.length > 1) {
            if (typeof args[1].body === 'string') {
                args[1].headers = customHeadersJSON;
            } else {
                args[1].headers = customHeaders;
            }
        }
        // Await the response to check status
        const response = await originalFetch.apply(this, args);

        // Handle 401/403 globally
        if (
            response.status === 401 &&
            // Only redirect to login for requests to boranga api endpoints
            args[0] &&
            typeof args[0] === 'string' &&
            new URL(args[0], window.location.origin).pathname.startsWith('/api')
        ) {
            window.location.href =
                '/login/?next=' + encodeURIComponent(window.location.pathname);
        } else if (response.status === 403) {
            swal.fire({
                icon: 'error',
                title: 'Access Denied',
                text: 'You do not have permission to perform this action.',
            });
        }

        // Return the response so the caller can process it (e.g., await response.json())
        return response;
    };
})(fetch);

Vue.config.devtools = true
