<template id="organisation_dashboard">
    <div class="row">
        <div class="col-sm-12">
            <FormSection
                :form-collapse="false"
                label="Organisations"
            >
                <div class="panel panel-default">
                    <div class="row">
                        <div class="col-lg-12">
                            <datatable ref="organisation_datatable" :id="datatable_id" :dtOptions="organisation_options" :dtHeaders="organisation_headers"/>
                        </div>
                    </div>
                </div>
            </FormSection>
        </div>
    </div>
</template>
<script>
import { v4 as uuid } from 'uuid';
import datatable from '@vue-utils/datatable.vue'
import {
    api_endpoints,
    helpers
}from '@/utils/hooks'
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name: 'OrganisationDashTable',
    data() {
        let vm = this;
        return {
            oBody: 'oBody' + uuid(),
            datatable_id: 'organisation-datatable-'+uuid(),
            organisation_headers: ["Name", "ABN", "Address", "Action"],
            organisation_options:{
                serverSide: true,
                searchDelay: 1000,
                lengthMenu: [ [10, 25, 50, 100], [10, 25, 50, 100] ],
                order: [
                    [0, 'asc']
                ],
                tableID: 'organisation-datatable-'+uuid(),
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                ajax: {
                    "url": helpers.add_endpoint_join(api_endpoints.organisations_paginated,'datatable_list/?format=datatables'),
                    "dataSrc": "data",
                },
                columns: [
                    {
                        data: "name",
                        name: "organisation__name"
                    },
                    {
                        data: "abn",
                        name: "organisation__abn"
                    },
                    {
                        data: "address_string",
                        mRender:function (data,type,full) {
                            if (data) {
                                return data;
                            }
                            return ''
                        },
                        orderable: false,
                        searchable: false // handled by filter_queryset override method - class OrganisationFilterBackend
                    },
                    {
                        data: "id",
                        mRender:function (data,type,full) {
                            let links = '';
                            links +=  `<a href='/internal/organisations/${full.id}'>View</a><br/>`;
                            return links;
                        },
                        orderable: false,
                        searchable: false
                    }
                ],
                processing: true,
                initComplete: function () {
                }
            }
        }
    },
    components: {
        FormSection,
        datatable
    },
    mounted: function(){
        let vm = this;
        $( 'a[data-toggle="collapse"]' ).on( 'click', function () {
            var chev = $( this ).children()[ 0 ];
            window.setTimeout( function () {
                $( chev ).toggleClass( "glyphicon-chevron-down glyphicon-chevron-up" );
            }, 100 );
        });
    }
}
</script>

