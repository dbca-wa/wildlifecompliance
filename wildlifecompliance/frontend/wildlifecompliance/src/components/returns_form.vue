<template lang="html">
    <div>
        <ReturnsRendererForm
            :form_width="form_width"
        />
        <slot></slot>
    </div>
</template>

<script>
    import Vue from 'vue'
    import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
    
    import '@/scss/forms/form.scss';
    import ReturnsRendererForm from '@/components/common/returns_renderer.vue';
    export default {
        components: {
            ReturnsRendererForm,
        },
        props:{
            form_width: {
                type: String,
                default: 'col-md-8'
            }
        },
    }
</script>
