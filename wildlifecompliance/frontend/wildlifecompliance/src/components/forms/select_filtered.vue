<!--
This component supports multi select from a large list. The large list is filtered by the first three characters in the
search and calls the server api with a filtered_list_url.
-->
<template lang="html">
    <div>
        <div class="form-group">
            <label :id="id" for="label" class="inline" style="white-space: pre-line;">{{label}} <HelpTextUrl :help_text_url="help_text_url" /></label>

            <template v-if="help_text">
                <HelpText :help_text="help_text" />
            </template>

            

            <CommentBlock 
                :label="label"
                :name="name"
                :field_data="field_data"
                />

            <template v-if="readonly">
                <select v-if="!isMultiple" disabled ref="selectB" :id="selectid" :name="name" class="form-control" :data-conditions="cons" style="width:100%">
                    <!-- <option value="">Select...</option> -->
                    <option v-for="(op, idx1) in species"  :value="op.value" @change="handleChange" :selected="op.value == value" v-bind:key="`value_${op.value}_${idx1}`">{{ op.label }}</option>
                </select>
                <select v-else disabled ref="selectB" :id="selectid" class="form-control" multiple style="width:100%">
                    <!-- <option value="">Select...</option> -->
                    <option v-for="(op, idx1) in species"  :value="op.value" :selected="multipleSelection(op.value)" v-bind:key="`value_${op.value}_${idx1}`">{{ op.label }}</option>
                </select>
                <template v-if="isMultiple">
                    <input v-for="(v, idx2) in value" input type="hidden" :name="name" :value="v" :required="isRequired" v-bind:key="`value_${v}_${idx2}`"/>
                </template>
                <template v-else>
                    <input type="hidden" :name="name" :value="value" :required="isRequired"/>
                </template>
            </template>
            <template v-else>
                <select v-if="!isMultiple" ref="selectB" :id="selectid" :name="name" class="form-control" :data-conditions="cons" style="width:100%" :required="isRequired">
                    <!-- <option value="">Select...</option> -->
                    <option v-for="(op, idx1) in species" :value="op.value" selected="selected" v-bind:key="`value_${op.value}_${idx1}`">{{ op.label }}</option>
                </select>
                <select v-else ref="selectB" :id="selectid" :name="name" class="form-control" multiple style="width:100%" :required="isRequired">
                    <!-- <option value="">Select...</option> -->
                    <option v-for="(op, idx1) in species" :value="op.value" selected="selected" v-bind:key="`value_${op.value}_${idx1}`">{{ op.label }}</option>
                </select>
            </template>
        </div>

    </div>
</template>

<script>
import Vue from 'vue';
import { mapActions, mapGetters } from 'vuex';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import CommentBlock from './comment_block.vue';

// var select2 = require('select2');
// require("select2/dist/css/select2.min.css");
// require("select2-bootstrap-theme/dist/select2-bootstrap.min.css");

export default {
    props: {
        "label": {
            type: String
        },
        "name": {
            type: String
        },
        "field_data": {
            type: Object,
            required: true
        },
        "options": {
            type: Array,
            required: true,
            default:function () {
                return [];
            }
        },
        "readonly": {
            type: Boolean,
            default: false
        },
        "id": {
            type: String,
        },
        "isRequired": {
            type: Boolean,
            default: false
        },
        "help_text": {
            type: String,
        },
        "help_text_url": {
            type: String,
        },
        "isMultiple":{
            default:function () {
                return false;
            }
        },
        "handleChange":null,
        "filtered_list_url": {
            type: String
        },
    },
    data:function () {
        let vm =this;
        return{
            selected: (this.isMultiple) ? [] : "",
            selectid: "select"+vm._uid,
            multipleSelected: [],
        }
    },
    computed:{
        ...mapGetters([
            'application_id',
            'renderer_form_data',
        ]),
        cons: function () {
            return JSON.stringify(this.field_data);
        },
        value: function() {
            return this.field_data.value;
        },
        species: function() {
            let results = [];
            let specie = {};
            if (Array.isArray(this.field_data.value)){
                for (let i=0; i < this.field_data.value.length; i++){
                    specie = {
                        'value': this.field_data.value[i],
                        'label': this.field_data.value[i],
                    }
                    if (this.field_data.value[i] != ''){
                        results[i] = specie 
                    }
                }

            }
            else {

                specie = {
                    'value': this.field_data.value,
                    'label': this.field_data.value,
                }
                if (this.field_data.value != ''){
                    results[0] = specie 
                }

            }
            let unique_results = [...new Set(results)]
            return unique_results
        },
    },
    components: { HelpText, HelpTextUrl, CommentBlock },
    methods:{
        multipleSelection2: function(val){
            if (Array.isArray(this.options)){
                if (this.species.find(v => v == val)){
                    return true;
                }
            }else{
                if (this.species == val){return true;}
            }
            return false;
        },
        multipleSelection: function(val){
            if (Array.isArray(this.field_data.value)){
                let selected = '0'
                for (let i=0; i < this.field_data.value.length; i++){
                    if (this.field_data.value[i] == val){
                        selected = this.field_data.value[i];
                        break;
                    }
                }
                if (this.species.find(v => v.value == selected && v.value === val)){
                    return true;
                }
            }else{
                let species = [this.field_data.value]

                if (species.find(v => v.value === this.field_data.value && v.value === val)){
                    return true;
                }
            }
            return false;
        },
        init:function () {
            let vm =this;
            vm.multipleSelected = vm.field_data.value;
            let data = '';
            setTimeout(function (e) {
                   $('#'+vm.selectid).select2({
                       "theme": "bootstrap",
                       tags: true,
                    //    allowClear: true,
                       placeholder:"Select...",
                       minimumInputLength: 3,
                       type: 'GET',
                       dataType: 'json',
                       ajax: {
                           url: vm.filtered_list_url
                       },
                   }).
                   on("select2:select",function (e) {
                        e.stopImmediatePropagation();
                        e.preventDefault();
                        var selected = $(e.currentTarget);
                        //vm.handleChange(selected[0])
                        // if( vm.isMultiple){
                        vm.field_data.value = vm.multipleSelected = selected.val();
                        // }
                   }).
                   on("select2:unselect",function (e) {
                        e.stopImmediatePropagation();
                        e.preventDefault();
                        var selected = $(e.currentTarget);
                        vm.handleChange(selected[0])
                        // if( vm.isMultiple){
                        vm.field_data.value = vm.multipleSelected = selected.val();
                        // }
                   });
                   if (vm.value) {
                       vm.handleChange(vm.$refs.selectB);
                   }
               },100);
        },
    },
    updated:function (){
        this.$nextTick(() => {
            this.field_data.value = this.multipleSelected[0] ? this.multipleSelected : this.field_data.value;
        });
    },
    mounted:function () {
        this.init();
    }
}
</script>

<style lang="css">
.select2-container {
    width: 100% !important;
}

input {
    box-shadow:none;
}
</style>

