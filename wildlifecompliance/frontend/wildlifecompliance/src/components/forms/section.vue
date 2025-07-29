<template lang="html">
    <FormSection
        :form-collapse="false"
        :label=label
    >
        <div class="panel panel-default" >
          <slot></slot>
        </div>
    </FormSection>
</template>

<script>
import FormSection from "@/components/forms/section_toggle.vue";
export default {
    name:"FormSection",
    props:["label","Index"],
    data:function () {
        return {
            title:"Section title",
            eventInitialised: false
        }
    },
    components: {
        FormSection,
    },
    computed:{
        section_id:function () {
            return "section_"+this.Index
        }
    },
    updated:function () {
        let vm = this;
        vm.$nextTick(()=>{
            if (!vm.eventInitialised){
                $('.panelClicker[data-toggle="collapse"]').on('click',function () {
                    var chev = $(this).children()[0];
                    window.setTimeout(function () {
                        $(chev).toggleClass("glyphicon-chevron-down glyphicon-chevron-up");
                    },100);
                });
                this.eventInitialised = true;
            }
        });
    }
}
</script>

<style lang="css">
    h3.panel-title{
        font-weight: bold;
        font-size: 25px;
        padding:20px;
    }
</style>
