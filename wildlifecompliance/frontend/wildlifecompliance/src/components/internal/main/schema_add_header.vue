<template lang="html">
    <div class="panel panel-primary">
        <div class="panel-heading">
            <h4 class="panel-title">Headers
                <a class="panelClicker" :href="`#`+pHeaderBody" data-toggle="collapse" data-parent="#userInfo" expanded="true" :aria-controls="pHeaderBody">
                    <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                </a>
            </h4>
        </div>
        <div class="panel-body panel-collapse collapse" :id="``+pHeaderBody">
            <div class="row">
                <div v-for="(h, hidx) in addedHeaders" v-bind:key="`h_${hidx}`" >

                    <div class="col-md-12">&nbsp; </div>
                    <div class="col-md-12">
                        <div class="col-md-3">
                            <label v-if="hidx===0" class="control-label pull-left" >Add Headers</label>
                        </div>
                        <div class="col-md-3">
                            <input type='text' class="form-control" v-model="h.label" />
                        </div>
                        <div class="col-md-3">
                            <select class="form-control" :ref="`header_answer_type_${hidx}`" :name="`select-answer-type-${hidx}`" v-model="h.value" @change="setShowAdditional(h, h.value)">
                                <option v-for="(ha, haidx) in answerTypes" :value="ha.value" >{{ha.label}}</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <a v-if="hidx!==0" class="delete-icon fa fa-trash-o" style="cursor: pointer; color:red;" title="Delete row" @click.prevent="removeHeader(hidx)"></a>
                            <button v-if="hidx===0" class="btn btn-link pull-right" :name="`add_header_link_1`" @click.prevent="addHeader()">[ Add Another ]</button>
                        </div>
                        <div class="col-md-12">&nbsp; </div>
                        <div class="col-md-12" v-if="h.showOptions">
                            <div class="col-md-3">&nbsp; </div>
                            <div class="col-md-9">
                                <SchemaOption  ref="`schema_option_${hidx}`" :addedOptions="h.options" :canAddMore="true" />
                            </div>

                        </div>
                    </div>

                </div>
            </div>
        </div>
    </div>
</template>

<script>
import SchemaOption from './schema_add_option.vue'
export default {
    name:"schema-add-header",
    components: {
        SchemaOption,
    },
    props: {
        addedHeaders: Array,
        answerTypes: Array,
    },
    data:function () {
        let vm = this;
        return {
            pHeaderBody: 'pHeaderBody' + vm._uid,
            addedHeader: {
                label: '',
                value: '',
                options:'',
                showOptions: false,
            },
            showOptions: false,
            addedOption: {
                id: '',
                label: '',
                value: '',
            },
        };
    },
    computed:{
    },
    methods: {
        addHeader: function() {
            const newHeader = Object();
            newHeader.label = '';
            newHeader.value = '';
            newHeader.options=[];
            newHeader.showOptions=false;
            const newOption=Object();
            newOption.id = ''
            newOption.label = ''
            newOption.value = ''
            let newOption1 = Object.assign(newOption)
            newHeader.options.push(newOption1);
            this.addedHeaders.push(newHeader)
        },
        removeHeader: function(id=0) {
            this.addedHeaders.splice(id, 1)
        },
        setShowAdditional: function(header,selected_id) {
            const option = ['radiobuttons','select', 'multi-select']
            const q_type = this.answerTypes.find( t => t.value === selected_id && (option.includes(t.value)))

            header.showOptions = q_type && option.includes(q_type.value) ? true : false

            // if (this.showOptions && this.isNewEntry) {
            //     this.addedOption.id = ''
            //     this.addedOption.label = ''
            //     this.addedOption.value = ''
            //     let newOption = Object.assign(this.addedOption)
            //     this.addedOptions.push(newOption);          
            // }
            if (header.showOptions) {
                if(header.isNewEntry){
                    const newOption=Object();
                    newOption.id = ''
                    newOption.label = ''
                    newOption.value = ''
                    let newOption1 = Object.assign(newOption)
                    header.options.push(newOption1); 
                }
                else{//if in edit mode but has no options added previously then allow to add options.
                    if(header.options.length==0){
                        const newOption=Object();
                        newOption.id = ''
                        newOption.label = ''
                        newOption.value = ''
                        let newOption1 = Object.assign(newOption)
                        header.options.push(newOption1);
                    }
                }
                         
            }

        },
    },
}
</script>