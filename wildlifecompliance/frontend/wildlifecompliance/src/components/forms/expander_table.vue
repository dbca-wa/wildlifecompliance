<template lang="html">
    <div class="form-group">
        <label :id="id" for="label" class="expander-label" style="white-space: pre-line;">{{ label }} <HelpTextUrl :help_text_url="help_text_url" /></label>

        <template v-if="help_text">
            <HelpText :help_text="help_text" />
        </template>
        
        <CommentBlock 
            :label="commentLabel"
            :name="name"
            :field_data="field_data"
            />
        <div :class="tableClass"> 
            <div class="row header-titles-row">
            
                <div v-for="(header, index) in component.header"
                    :class="`col-md-${getColXSValue(header.colSize)} truncate-text`"
                    v-bind:key="`expander_header_${component.name}_${index}`">
                        {{ header.label }}
                </div>
            </div>
            <div class="expander-table" v-for="(table, tableIdx) in expanderTables">
                <div class="row header-row">
                    <div v-for="(header, index) in component.header"
                        :class="`col-md-${getColXSValue(header.colSize)}`"
                        v-bind:key="`expander_header_${component.name}_${index}`">
                            <span v-if="index===0 && component.expander && component.expander.length>0" :class="`expand-icon ${isExpanded(table) ? 'collapse' : ''}`"
                                v-on:click="toggleTableVisibility(table)"></span>

                            <span class="header-contents" :title="value.toString()">
                                <renderer-block
                                :component="removeLabel(header)"
                                :json_data="value"
                                :instance="table"
                                :isTableField="true"
                                v-bind:key="`expander_header_contents_${component.name}_${index}`"
                                />
                            </span>
                            <button v-if="tableIdx && index == component.header.length-1 && !readonly" title="Delete row" type="button" class="btn btn-danger float-end" style="margin-bottom: 5px"
                                @click.prevent="removeTable(table)"><i class="bi bi-trash"></i></button>
                    </div>
                </div>
                <div :class="{'hidden': !isExpanded(table)}">
                    <div class="row expander-row" v-for="(subcomponent, index) in component.expander" v-bind:key="`expander_row_${component.name}_${index}`">
                        <div class="col-md-12">
                            <renderer-block
                                :component="subcomponent"
                                :json_data="value"
                                :instance="table"
                                v-bind:key="`expander_contents_${component.name}_${index}`"
                                />
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <div class="row" v-if="!readonly">
            <div class="col-md-3">
            <input type="button" value="Add New" class="btn btn-primary add-new-button"
                @click.prevent="addNewTable">
            </div>
        </div>
    </div>
</template>

<script>
import CommentBlock from './comment_block.vue';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import { mapGetters, mapActions } from 'vuex';
import '@/scss/forms/expander_table.scss';

const ExpanderTable = {
    props:{
        name: String,
        label: String,
        id: String,
        isRequired: String,
        help_text: String,
        help_text_url: String,
        component: {
            type: Object,
            required: true
        },
        field_data: {
            type: Object,
            required: true
        },
        readonly:Boolean,
    },
    components: {
        CommentBlock,
        HelpText,
        HelpTextUrl
    },
    data(){
        return {
            expanded: {},
        };
    },
    methods: {
        ...mapActions([
            'removeFormInstance',
            'setFormValue',
            'refreshApplicationFees',
        ]),
        isExpanded: function(tableId) {
            return this.expanded[tableId];
        },
        toggleTableVisibility: function(tableId) {
            if(this.expanded[tableId]) {
                this.$delete(this.expanded, tableId);
            }
            else {
                this.$set(this.expanded, tableId, true);
            }
        },
        removeTable: function(tableId) {
            if(this.expanded[tableId]) {
                this.$delete(this.expanded, tableId);
            }
            this.removeFormInstance(
                this.getInstanceName(tableId)
            );
            this.updateVisibleTables(
                this.existingTables.filter(table => table != tableId)
            );
            // this.refreshApplicationFees();
        },
        addNewTable: function(params={}) {
            let { tableId } = params;
            if(!tableId) {
                tableId = this.getTableId(this.lastTableId+1);
            }
            this.existingTables.push(tableId);
            this.updateVisibleTables(
                this.existingTables
            );
            // this.refreshApplicationFees();
        },
        updateVisibleTables: function(tableList) {
            this.setFormValue({
                key: this.component.name,
                value: {
                    "value": tableList,
                }
            });
        },
        getTableId: function(tableIdx) {
            return `${this.id}_table_${tableIdx}`;
        },
        getInstanceName: function(tableId) {
            return `__instance-${tableId}`
        },
        removeLabel: function(header) {
            let newHeader = {...header};
            delete newHeader['label'];
            return newHeader;
        },
        getColXSValue: function (colSize){
            const fixedValue = this.component.header.length > 4 ? 2 : Math.floor(12 / this.component.header.length);
            const hasNullSize = this.component.header.some(obj => obj.colSize ? obj.colSize === null : true);
            if(hasNullSize){
                return fixedValue;
            }
            return colSize;
        },
    },
    computed:{
        ...mapGetters([
            'canViewComments',
            'canViewDeficiencies',
            'canEditDeficiencies',
            'getFormValue',
        ]),
        lastTableId: function() {
            if(!this.existingTables.length) {
                return 0;
            }
            let lastId = 0;
            this.existingTables.map(tableId => tableId[tableId.length-1] > lastId && (lastId = tableId[tableId.length-1]));
            return parseInt(lastId, 10);
        },
        existingTables: function() {
            return this.getFormValue(this.component.name) || [];
        },
        expanderTables: function() {
            if(!this.existingTables.length) {
                this.addNewTable();
            }
            return this.existingTables;
        },
        value: function() {
            return this.field_data;
        },
        showExpanderIcon: function() {
            return false
        },
        tableClass: function(){
            const class_name = this.component.header.length > 6 ? "horizontal-scrollable" : "no-scroll-background";
            return class_name;
        },
        commentLabel: function(){
            let commentLabel = this.label
            if (this.label === undefined || this.label == "") {
                commentLabel = "Comment"
            }
            return commentLabel;
        }
    },
}

export default ExpanderTable;
</script>
<style>
.no-scroll-background {
    background-color: #efefef;
}
.horizontal-scrollable {
    overflow-x: auto;
    white-space: nowrap;
    background-color: #efefef;
}
.horizontal-scrollable > .row > .col-md-2 {
    display: inline-block;
    float: none;
}
.horizontal-scrollable > .expander-table> .row > .col-md-2 {
    display: inline-block;
    float: none;
}

</style>
