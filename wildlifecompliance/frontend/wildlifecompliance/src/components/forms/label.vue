<template lang="html">
    <div class="form-group">
        <label :id="id" class="fw-bold" for="label" style="white-space: pre-line;">{{ value }} <HelpTextUrl v-if="help_text_url" :help_text_url="help_text_url" /></label>
    </div>
</template>

<script>
import HelpTextUrl from './help_text_url.vue';
export default {
    props:["value", "id", "help_text_url"],
    components: { HelpTextUrl, },
}
</script>

<style lang="css">
</style>
