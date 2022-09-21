<template lang="html">
    <div class="panel panel-primary">
        <div class="panel-heading">
            <h4 class="panel-title">Expanders
                <a class="panelClicker" :href="`#`+pExpanderBody" data-toggle="collapse" data-parent="#userInfo" expanded="true" :aria-controls="pExpanderBody">
                    <span class="glyphicon glyphicon-chevron-down pull-right "></span>
                </a>
            </h4>
        </div>
        <div class="panel-body panel-collapse collapse" :id="``+pExpanderBody">
            <div class="row">
                <div v-for="(e, eidx) in addedExpanders" v-bind:key="`e_${eidx}`">

                    <div class="col-md-12">&nbsp; </div>
                    <div class="col-md-12">
                        <div class="col-md-3">
                            <label v-if="eidx===0" class="control-label pull-left" >Add Expanders</label>
                        </div>
                        <div class="col-md-3">
                            <input type='text' class="form-control" v-model="e.label" />
                        </div>
                        <div class="col-md-3">
                            <select class="form-control" :ref="`expander_answer_type_${eidx}`" :name="`select-answer-type-${eidx}`" v-model="e.value" @change="setShowAdditional(e, e.value)">
                                <option v-for="(ea, eaidx) in answerTypes" :value="ea.value" >{{ea.label}}</option>
                            </select>
                        </div>
                        <div class="col-md-3">
                            <a v-if="eidx!==0" class="delete-icon fa fa-trash-o" style="cursor: pointer; color:red;" title="Delete row" @click.prevent="removeExpander(eidx)"></a>
                            <button v-if="eidx===0" class="btn btn-link pull-right" :name="`add_expander_link_1`" @click.prevent="addExpander()">[ Add Another ]</button>
                        </div>
                        <div class="col-md-12">&nbsp; </div>
                        <div class="col-md-12" v-if="e.showOptions">
                            <div class="col-md-3">&nbsp; </div>
                            <div class="col-md-9">
                                <SchemaOption  ref="`schema_option_${eidx}`" :addedOptions="e.options" :canAddMore="true" />
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
    name:"schema-add-expander",
    components: {
        SchemaOption,
    },
    props: {
        addedExpanders: Array,
        answerTypes: Array,
    },
    data:function () {
        let vm = this;
        return {
            pExpanderBody: 'pExpanderBody' + vm._uid,
            addedExpander: {
                label: '',
                value: '',
                conditions: null,
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
        addExpander: function() {
            const newExpander = Object()
            newExpander.label = '';
            newExpander.value = '';
            newExpander.conditions = null;
            newExpander.options=[];
            newExpander.showOptions=false;
            const newOption=Object();
            newOption.id = ''
            newOption.label = ''
            newOption.value = ''
            let newOption1 = Object.assign(newOption)
            newExpander.options.push(newOption1);
            this.addedExpanders.push(newExpander)
        },
        removeExpander: function(id=0) {
            this.addedExpanders.splice(id, 1)
        },
        setShowAdditional: function(expander,selected_id) {
            const option = ['radiobuttons','select', 'multi-select']
            const q_type = this.answerTypes.find( t => t.value === selected_id && (option.includes(t.value)))

            expander.showOptions = q_type && option.includes(q_type.value) ? true : false

            // if (this.showOptions && this.isNewEntry) {
            //     this.addedOption.id = ''
            //     this.addedOption.label = ''
            //     this.addedOption.value = ''
            //     let newOption = Object.assign(this.addedOption)
            //     this.addedOptions.push(newOption);          
            // }
            if (expander.showOptions) {
                if(expander.isNewEntry){
                    const newOption=Object();
                    newOption.id = ''
                    newOption.label = ''
                    newOption.value = ''
                    let newOption1 = Object.assign(newOption)
                    expander.options.push(newOption1); 
                }
                else{//if in edit mode but has no options added previously then allow to add options.
                    if(expander.options.length==0){
                        const newOption=Object();
                        newOption.id = ''
                        newOption.label = ''
                        newOption.value = ''
                        let newOption1 = Object.assign(newOption)
                        expander.options.push(newOption1);
                    }
                }
                         
            }

        },
        initEventListeners: function(){
                self=this;
                if(self.addedExpanders){
                for(var i=0; i<self.addedExpanders.length; i++){
                    self.setShowAdditional(self.addedExpanders[i], self.addedExpanders[i].answer_type);
                }
            }
            },
    },
    mounted: function() {
        this.$nextTick(() => {
            self=this;
            //this.initEventListeners();
        });
    }
}
</script>