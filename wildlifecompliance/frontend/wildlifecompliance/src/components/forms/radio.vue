<template lang="html">
    <div v-if="readonly">
        <div class="radio form-check">
            <label class="form-check-label" :id="id">{{ label}}</label>
            <input class="form-check-input" ref="radioB" :name="name" disabled type="radio" :value="value" @change="handleChange"  :required="isRequired" :data-conditions="options" :checked="isChecked"/>            
        </div>
        <input type="hidden" :name="name" :value="savedValue.value"/>
    </div>
    <div v-else>
        <div class="radio form-check">
            <label class="form-check-label" :id="id">{{ label}}</label>
            <input class="form-check-input" ref="radioB" :name="name" type="radio" :value="value" @change="handleChange"  :required="isRequired" :data-conditions="options" :checked="isChecked"/>
        </div>
    </div>
</template>

<script>
export default {
    name:"radiobuttons",
    props:["value","label", "id", "name","isRequired","handleChange","conditions","savedValue","readonly"],
    computed:{
        isChecked:function () {
            if (this.value == this.savedValue.value) {
                return true
            }
            return null
        },
        options:function () {
            return JSON.stringify(this.conditions);
        }
    },
    mounted:function () {
        if (this.value == this.savedValue.value) {
            var input = this.$refs.radioB;
            var e = document.createEvent('HTMLEvents');
            e.initEvent('change', true, true);
            var disabledStatus = input.disabled;
            try {
                /* Firefox will not fire events for disabled widgets, so (temporarily) enabling them */
                if(disabledStatus) {
                    input.disabled = false;
                }
                input.dispatchEvent(e);
            } finally {
                if(disabledStatus) {
                    input.disabled = true;
                }
            }
        }
    }
}
</script>

<style lang="css">
    input {
        box-shadow:none;
    }
</style>
