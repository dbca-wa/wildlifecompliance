<template lang="html">
    <div class="row">
        <ReturnsRendererForm
            :form_width="form_width"
        />
        <slot></slot>
    </div>
</template>

<script>
   
    import {
  api_endpoints,
  helpers
}
from '@/utils/hooks'
    
    import '@/scss/forms/form.scss';
    import ReturnsRendererForm from '@common-components/returns_renderer.vue';
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
