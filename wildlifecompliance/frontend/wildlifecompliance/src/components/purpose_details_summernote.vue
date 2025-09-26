
<template lang="html">
    <div class="summernote-wrapper">
        <div class="summernote-div"></div>
        <textarea class="summernote-text" v-model="formatted_text" style="display:none"></textarea>
    </div>
</template>

<script>

export default {
    emits: ['update-formatted-text'],
    props: {
        formatted_text_prop: {
            type: String,
            default: ""
        },
        purpose_index: {
            type: Number,
            required: true,
        },
        activity_index: {
            type: Number,
            required: true, //technically not also required, but we substitute it anyway
        },
        species_index: {
            type: Number,
            required: true,
        }
    },
    data: function () {
        return {
            pushed: 0, // if content pushed from vue 
            changed: 0, // if content changed in summernote
            $summernoterElement : null,
            raw_text: "",
            summernote_display: null,
        }
    },
    computed: {
        formatted_text: function() {
            return this.formatted_text_prop;
        }
    },
    watch: {
        formatted_text: {
            handler(val){
                if (this.changed > 0) {
                    this.changed--;
                } else {
                    this.pushed++;
                    this.setText(this.formatted_text);
                }
            },
            deep: true
        },
    },
    methods: {
        setText: function (text) {
            this.$summernoteElement.summernote('code', text);
        },
        updateFormatedText: function (_, contents) {
            if (this.pushed > 0) {
                    this.pushed--;
            } else {
                this.changed++;
                this.$emit('update-formatted-text', {"formatted_text":contents, "purpose_index":this.purpose_index, "activity_index":this.activity_index, "species_index":this.species_index})
            }
        }
    },
    mounted: function() {
        let config = {};
        this.$summernoteElement = $(this.$el).find('.summernote-div').first();
        config.minHeight = null;
        config.maxHeight = null;
        config.toolbar =  [
                ['view', ['codeview']],
                ['style', ['bold', 'italic', 'style']],
                ['para', ['ul', 'ol']],
                ['table', ['table']],
            ]; 
        // init the editor
        this.$summernoteElement.summernote(config);
        // set formatted_text
        this.$summernoteElement.summernote('code', this.formatted_text);
        // set callback to pass event back to parent 
        this.$summernoteElement.on('summernote.change', this.updateFormatedText);
    }
}
</script>