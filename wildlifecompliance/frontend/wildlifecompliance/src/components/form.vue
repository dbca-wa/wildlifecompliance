<template lang="html">
    <div>
        <RendererForm
            :withSectionsSelector="withSectionsSelector"
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
    import RendererForm from '@common-components/renderer.vue';
    export default {
        components: {
            RendererForm,
        },
        props:{
            withSectionsSelector:{
                type: Boolean,
                default: true
            },
            form_width: {
                type: String,
                default: 'col-md-9'
            }
        },
    }
</script>
