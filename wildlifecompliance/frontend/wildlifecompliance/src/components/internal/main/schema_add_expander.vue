<template lang="html">
    <FormSection
        :form-collapse="false"
        label="Expanders"
    >
        <div class="panel panel-primary">
            <div class="row">
                <div v-for="(e, eidx) in addedExpanders" v-bind:key="`e_${eidx}`">

                    <div class="col-md-12">&nbsp; </div>
                    <div class="col-md-12">
                        <div class="col-md-3">
                            <label v-if="eidx===0" class="control-label float-start" >Add Expanders</label>
                        </div>
                        <div class="col-md-3">
                            <input type='text' class="form-control" v-model="e.label" />
                        </div>
                        <div class="col-md-3">
                            <select class="form-control" :ref="`expander_answer_type_${eidx}`" :name="`select-answer-type-${eidx}`" v-model="e.value" >
                                <option v-for="(ea, eaidx) in answerTypes" :value="ea.value" >{{ea.label}}</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <a v-if="eidx!==0" class="delete-icon fa fa-trash-o" style="cursor: pointer; color:red;" title="Delete row" @click.prevent="removeExpander(eidx)"></a>
                            <button v-if="eidx===0" class="btn btn-link float-end" :name="`add_expander_link_1`" @click.prevent="addExpander()">[ Add Another ]</button>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    </FormSection>
</template>

<script>
import { v4 as uuid } from 'uuid';
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name:"schema-add-expander",
    props: {
        addedExpanders: Array,
        answerTypes: Array,
    },
    data:function () {
        let vm = this;
        return {
            pExpanderBody: 'pExpanderBody' + uuid(),
            addedExpander: {
                label: '',
                value: '',
                conditions: null,
            },
        };
    },
    components: {
        FormSection,
    },
    methods: {
        addExpander: function() {
            const newExpander = Object()
            newExpander.label = '';
            newExpander.value = '';
            newExpander.conditions = null;
            this.addedExpanders.push(newExpander)
        },
        removeExpander: function(id=0) {
            this.addedExpanders.splice(id, 1)
        },
    },
}
</script>