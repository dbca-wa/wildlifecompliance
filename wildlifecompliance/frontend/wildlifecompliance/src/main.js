// The Vue build version to load with the `import` command
// (runtime-only or standalone) has been set in webpack.base.conf with an alias.
import Vue from 'vue';
import resource from 'vue-resource';
import App from './App';
import router from './router';
import helpers from '@/utils/helpers';
import api_endpoints from './api';
import store from './store';
import RendererBlock from '@/components/common/renderer_block.vue';
import ComplianceRendererBlock from '@/components/common/compliance_renderer_block.vue';
import VueScrollTo from 'vue-scrollto';
import Affix from 'vue-affix';
import Vuelidate from 'vuelidate'

import { extendMoment } from 'moment-range';
 
 import jsZip from 'jszip';
 window.JSZip = jsZip;
 
 import  'datatables.net';
 import 'datatables.net-bs';
 import 'datatables.net-responsive-bs';
 import 'datatables.net-buttons/js/dataTables.buttons.js';
 import 'datatables.net-buttons/js/buttons.html5.js';
 
 require("datatables.net-bs/css/dataTables.bootstrap.css");
 require("datatables.net-responsive-bs/css/responsive.bootstrap.css");
 
 import 'select2';
 import "sweetalert2/dist/sweetalert2.css";
 import 'jquery-validation';
 
 import 'select2-bootstrap-theme/dist/select2-bootstrap.min.css';
 
 extendMoment(moment);

require( '../node_modules/bootstrap/dist/css/bootstrap.css' );
//require('../node_modules/eonasdan-bootstrap-datetimepicker/build/css/bootstrap-datetimepicker.min.css')
require( '../node_modules/font-awesome/css/font-awesome.min.css' );

//Vue.config.devtools = true;
Vue.config.productionTip = false
Vue.use( resource );
Vue.use( VueScrollTo );
Vue.use( Affix );
Vue.use(Vuelidate)
Vue.component('renderer-block', RendererBlock);
Vue.component('compliance-renderer-block', ComplianceRendererBlock);

// ckeditor4 is installed in 'wildlifecompliance/templates/wildlifecompliance/base.html'
import CKEditor from 'ckeditor4-vue';
Vue.use( CKEditor );

// Add CSRF Token to every request
Vue.http.interceptors.push( function ( request, next ) {
  // modify headers
  if ( request.url != api_endpoints.countries ) {
    request.headers.set( 'X-CSRFToken', helpers.getCookie( 'csrftoken' ) );
  }

  // continue to next interceptor
  next();
} );

Vue.filter('toCurrency', function(value) {
                if (typeof value !== "number") {
                    return value;
                }
                var formatter = new Intl.NumberFormat('en-AU', {
                    style: 'currency',
                    currency: 'AUD',
                    minimumFractionDigits: 2
                });
                return formatter.format(value);
            });

var mapbox_access_token = '';

Vue.mixin({
    methods: {
        retrieveMapboxAccessToken: async function(){
            let ret_val = await $.ajax('/api/geocoding_address_search_token');
            return ret_val;
        }
    },
})

/* eslint-disable no-new */
Vue.prototype.current_tab = '';
window.vue = new Vue( {
    el: '#app',
    store,
    router,
    template: '<App/>',
    components: {
        App
    },
})

Vue.config.devtools = true
