
<template lang="html">
    <div class="summernote-wrapper">
        <div class="summernote-div"></div>
        <textarea class="summernote-text" v-model="formatted_text" style="display:none"></textarea>
    </div>
</template>

<script>

export default {
    props: {
        formatted_text: {
            type: String,
            default: ""
        },
        purpose_index: {
            type: Number,
            required: true,
        },
        activity_index: {
            type: Number,
            required: true,
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
            this.$summernoterElement.summernote('code', text);
        },
        updateFormatedText: function (_, contents) {
            if (this.pushed > 0) {
                    this.pushed--;
                } else {
                    this.changed++;
                    //this.formatted_text = contents;
                    this.$emit('update-formatted-text', {"formatted_text":this.formatted_text, "purpose_index":this.purpose_index, "activity_index":this.activity_index, "species_index":this.species_index})
                }
        }
    },
    mounted: function() {
        let config = {};
        this.$summernoterElement = $(this.$el).find('.summernote-div').first();
        config.minHeight = null;
        config.maxHeight = null;
        config.toolbar =  [
                ['style', ['bold', 'italic', 'underline', 'clear']],
                ['color', ['color']],
                ['para', ['ul', 'ol', 'paragraph']],
                ['height', ['height']]
            ]; 
        // init the editor
        this.$summernoterElement.summernote(config);
        // set formatted_text
        this.$summernoterElement.summernote('code', this.formatted_text);
        // set callback to pass event back to parent 
        this.$summernoterElement.on('summernote.change', this.updateFormatedText);
    }
}
</script>