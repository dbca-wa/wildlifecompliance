<template lang="html">
    <div class="top-buffer bottom-buffer">
        <div class="card mb-3">
            <div class="card-body border-bottom">
                <label :id="id" class="inline fw-bold">{{label}}</label>
                    <!--<i data-toggle="tooltip" v-if="help_text" data-placement="right" class="fa fa-question-circle" :title="help_text"> &nbsp; </i>-->
                <div v-if="help_text">
                    <HelpText :help_text="help_text" /> 
                </div>

                <div v-if="help_text_url">
                    <HelpTextUrl :help_text_url="help_text_url" /> 
                </div>
                
                <div class="children-anchor-point collapse in" style="padding-left: 0px"></div>
                <span :class="{'hidden':isRemovable}" v-if="isPreviewMode">
                    <a :id="'remove_'+name" >Remove {{label}}</a>
                </span>
                <div :class="{'row':true,}" style="margin-top:10px;" >
                    <div class="col-sm-12">
                        <slot></slot>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import HelpText from './help_text.vue'
import HelpTextUrl from './help_text_url.vue'
export default {
    name:"group",
    props:["label", "name", "id", "help_text", "help_text_url", "isRemovable","isPreviewMode","field_data"],
    data:function () {
        return{
            isExpanded:true
        }
    },
    components: {HelpText, HelpTextUrl},
    methods:{
        expand:function(e) {
            this.isExpanded = true;
        },
        minimize:function(e) {
            this.isExpanded = false;
        }
    },
}
</script>

<style lang="css">
    .collapse-link-top,.collapse-link-bottom{
        cursor:pointer;
    }
</style>
