<template lang="html">
    <div>
        <div class="form-group">
            <label :id="id" style="white-space: pre-line;">{{ label }} <HelpTextUrl :help_text_url="help_text_url" /></label>
            
            <template v-if="help_text">
                <HelpText :help_text="help_text" />
            </template>

            <CommentBlock 
                :label="label"
                :name="name"
                :field_data="field_data"
                />

            <div v-if="isTableField" class='date date-class'>
                <input type="date" :readonly="readonly" :name="name" class="form-control" placeholder="DD/MM/YYYY" v-model="value" :required="isRequired" :title="value"/>
            </div>
            <div v-else class='input-group date'>
                <input type="date" :readonly="readonly" :name="name" class="form-control" placeholder="DD/MM/YYYY" v-model="value" :required="isRequired" :title="value"/>
                <span class="input-group-addon">
                    <span class="glyphicon glyphicon-calendar"></span>
                </span>
            </div>
        </div>
    </div>
</template>

<script>

import moment from 'moment';
import CommentBlock from './comment_block.vue';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import { mapGetters } from 'vuex';
export default {
    props: ["name", "label", "id", "readonly", "help_text", "field_data", "conditions", "handleChange", "isRequired", "help_text_url", "isTableField"],
    data(){
        return {
        }
    },
    components: {CommentBlock, HelpText, HelpTextUrl},
    computed: {
        ...mapGetters([
            'canViewComments',
            'canViewDeficiencies',
            'canEditDeficiencies',
        ]),
        options: function() {
        return JSON.stringify(this.conditions);
        },
        value: {
            get: function() {
                return this.field_data.value;
            },
            set: function(value) {
                this.field_data.value = value;
            }
        },
    },
}
</script>

<style lang="css">
    input {
        box-shadow:none;
    }
.date-class {
    margin-top: -20px;
}
</style>
