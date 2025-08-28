<template>
    <div class="container" id="internalSanctionOutcomeDash">
        <FormSection :label="`Object`" :Index="`0`">

        <div class="row">
            <div class="col-md-3">
                <label class="">Type:</label>
                <select class="form-control" v-model="filterType">
                    <option v-for="option in artifact_types" :value="option.id" v-bind:key="option.id">
                        {{ option.display }}
                    </option>
                </select>
            </div>
            <div class="col-md-3">
                <label class="">Status:</label>
                <select class="form-control" v-model="filterStatus">
                    <option v-for="option in artifact_statuses" :value="option.id" v-bind:key="option.id">
                        {{ option.display }}
                    </option>
                </select>
            </div>
        </div>
        <div class="row">
            <div class="col-md-3">
                <label class="">Date from:</label>
                <div class="input-group date" ref="issueDateFromPicker">
                    <input type="date" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateFromPicker" />
                    <!--<span class="input-group-addon">
                        <span class="glyphicon glyphicon-calendar"></span>
                    </span>-->
                </div>
            </div>
            <div class="col-md-3">
                <label class="">Date to:</label>
                <div class="input-group date" ref="issueDateToPicker">
                    <input type="date" class="form-control" placeholder="DD/MM/YYYY" v-model="filterDateToPicker" />
                    <!--<span class="input-group-addon">
                        <span class="glyphicon glyphicon-calendar"></span>
                    </span>-->
                </div>
            </div>
            <div class="col-md-3 pull-right">
                <button @click.prevent="createArtifact" class="btn btn-primary pull-right">New Object</button>
            </div>
        </div>

        <div class="row">
            <div class="col-lg-12">
                <datatable ref="artifact_table" id="artifact-table" :dtOptions="dtOptions" :dtHeaders="dtHeaders" />
            </div>
        </div>
        </FormSection>
        <div v-if="createArtifactInitialised">
            <CreateArtifact
            ref="create_artifact"
            :readonlyForm="readonlyForm"
            v-bind:key="createArtifactBindId"
            initialTabSelected="artifact"
            />
        </div>
    </div>
</template>

<script>
import $ from 'jquery'
import datatable from '@/utils/vue/datatable.vue'
//import FormSection from "@/components/compliance_forms/section.vue";
import FormSection from "@/components/forms/section_toggle.vue";
import { api_endpoints, helpers, cache_helper } from '@/utils/hooks'
import CreateArtifact from "@/components/common/person_or_artifact_modal.vue";

export default {
    name: 'ArtifactTableDash',
    data() {
        let vm = this;
        return {
            artifact_types: [],
            artifact_statuses: [],

            filterType: 'all',
            filterStatus: 'all',
            filterDateFromPicker: '',
            filterDateToPicker: '',
            createArtifactInitialised: false,
            createArtifactBindId: '',

            dtOptions: {
                serverSide: true,
                searchDelay: 1000,
                lengthMenu: [ [10, 25, 50, 100, -1], [10, 25, 50, 100, "All"] ],
                order: [
                    [0, 'desc']
                ],
                language: {
                    processing: "<i class='fa fa-4x fa-spinner fa-spin'></i>"
                },
                responsive: true,
                processing: true,
                ajax: {
                    url: '/api/artifact_paginated/get_paginated_datatable/?format=datatables',
                    dataSrc: 'data',
                    data: function(d) {
                        d.type = vm.filterType;
                        d.artifact_status = vm.filterStatus;
                        d.date_from = vm.filterDateFromPicker;
                        d.date_to = vm.filterDateToPicker;
                    }
                },
                columns: [
                    {
                        data: 'number',
                        searchable: true,
                        orderable: true,
                    },
                    {
                        data: 'artifact_type_display',
                        searchable: true,
                        orderable: false,
                    },
                    {
                        data: 'identifier',
                        searchable: true,
                        orderable: true
                    },
                    {
                        data: 'artifact_date',
                        searchable: false,
                        orderable: true,
                        mRender: function (data, type, full) {
                            return data != '' && data != null ? moment(data).format('YYYY-MM-DD') : '';
                        }
                    },
                    {
                        data: 'number',
                        searchable: false,
                        orderable: false,
                        mRender: function (data, type,full){
                            return '---';
                        }
                    },
                    {
                        searchable: false,
                        orderable: false,
                        data: 'status'
                    },
                    {
                        searchable: false,
                        orderable: false,
                        data: 'digital_documents'
                    },
                    {
                        searchable: false,
                        orderable: false,
                        data: 'user_action',
                    }
                ],
            },
            dtHeaders: [
                'Number',
                'Type',
                'Identifier',
                'Date',
                'Custodian',
                'Status',
                'Documents',
                'Action',
            ],
        }
    },
    computed: {
        readonlyForm: function() {
            return false;
        },
    },
    watch: {
        filterType: function () {
            this.$refs.artifact_table.vmDataTable.draw();
        },
        filterStatus: function () {
            this.$refs.artifact_table.vmDataTable.draw();
        },
        filterDateFromPicker: function () {
            this.$refs.artifact_table.vmDataTable.draw();
        },
        filterDateToPicker: function () {
            this.$refs.artifact_table.vmDataTable.draw();
        },
    },
    created: async function() {
        this.constructOptionsType();
        this.constructOptionsStatus();
    },
    methods: {
        createArtifact: function() {
            console.log("create artifact")
            this.setCreateArtifactBindId()
            this.createArtifactInitialised = true;
            this.$nextTick(() => {
                this.$refs.create_artifact.isModalOpen = true;
            });
        },
        setCreateArtifactBindId: function() {
            let timeNow = Date.now()
            this.createArtifactBindId = 'artifact' + timeNow.toString();
        },
        constructOptionsType: async function() {
            let returned = await cache_helper.getSetCacheList('ArtifactTypes', '/api/artifact/types.json');
            Object.assign(this.artifact_types, returned);
            this.artifact_types.splice(0, 0, {id: 'all', display: 'All'});
        },
        constructOptionsStatus: async function() {
            let returned = await cache_helper.getSetCacheList('ArtifactStatuses', '/api/artifact/statuses.json');
            Object.assign(this.artifact_statuses, returned);
            this.artifact_statuses.splice(0, 0, {id: 'all', display: 'All'});
        },
    },
    components: {
        datatable,
        FormSection,
        CreateArtifact,
    },
}

</script>

<style>

</style>
