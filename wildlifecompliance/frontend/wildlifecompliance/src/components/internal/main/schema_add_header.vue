<template lang="html">
    <FormSection
        :form-collapse="false"
        label="Headers"
    >
        <div class="panel panel-primary">
            <div class="row">
                <div v-for="(h, hidx) in addedHeaders" v-bind:key="`h_${hidx}`" >

                    <div class="col-md-12">&nbsp; 
                        <div class="col-md-3">
                        </div>
                        <div class="col-md-2">
                        </div>
                        <div class="col-md-2">
                        </div>
                        <div class="col-md-2">
                            <i v-if="hidx == 0" class="fa fa-info-circle" aria-hidden="true" :title="colSizeInfoMsg" 
                                    style="cursor: pointer; color:crimson;"></i>
                        </div>
                    </div>
                        <div class="col-md-12">
                            <div class="col-md-3">
                                <label v-if="hidx===0" class="control-label pull-left" >Add Headers</label>
                            </div>
                            <div class="col-md-2">
                                <input type='text' class="form-control" v-model="h.label" />
                            </div>
                            <div class="col-md-2">
                                <select class="form-control" :ref="`header_answer_type_${hidx}`" :name="`select-answer-type-${hidx}`" v-model="h.value" >
                                    <option v-for="(ha, haidx) in answerTypes" :value="ha.value" >{{ha.label}}</option>
                                </select>
                            </div>
                            <div class="col-md-2">
                                <select class="form-control" :ref="`header_col_size_${hidx}`" :name="`select-col-size-${hidx}`" v-model="h.colSize" >
                                    <option v-for="(ha, haidx) in colSizeValues" :value="ha" >{{ha}}</option>
                                </select>
                            </div>
                            <div class="col-md-3">
                                <a v-if="hidx!==0" class="delete-icon fa fa-trash-o" style="cursor: pointer; color:red;" title="Delete row" @click.prevent="removeHeader(hidx)"></a>
                                <button v-if="hidx===0" class="btn btn-link pull-right" :name="`add_header_link_1`" @click.prevent="addHeader()">[ Add Another ]</button>
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
    name:"schema-add-header",
    props: {
        addedHeaders: Array,
        answerTypes: Array,
    },
    data:function () {
        let vm = this;
        return {
            pHeaderBody: 'pHeaderBody' + uuid(),
            addedHeader: {
                label: '',
                value: '',
                colSize:''
            },
            colSizeValues : Array.from({ length: 13 }, (_, index) => (index === 0 ? null : index)),
            colSizeInfoMsg: "When entering values for all headers, make sure the total sum is 12. You have two options for each header: either select a custom size or leave it blank. If you select a custom size, ensure that all headers have a value, and the sum of all selected values equals 12. If you want equal column sizes, leave all headers blank."
        };
    },
    components: {
        FormSection,
    },
    methods: {
        addHeader: function() {
            const newHeader = Object();
            newHeader.label = '';
            newHeader.value = '';
            newHeader.colSize = '';
            this.addedHeaders.push(newHeader)
        },
        removeHeader: function(id=0) {
            this.addedHeaders.splice(id, 1)
        },
    },
}
</script>