<template lang="html">
    <div>
        <div class="form-group">
            <label :id="id" :num_files="num_documents()" style="white-space: pre-line;">{{label}} <HelpTextUrl :help_text_url="help_text_url" /></label>
            <template v-if="help_text">
                <HelpText :help_text="help_text" />
            </template>

            

            <CommentBlock 
                :label="label"
                :name="name"
                :field_data="field_data"
                />

            <div v-if="files" :class="getClass">
                <div v-for="v in documents">
                    <p>
                        File: <a :href="v.file" target="_blank" :title="v.name.toString()">{{ truncatedName(v.name) }}</a>
                        <span v-if="!readonly && v.can_delete">
                            <a @click="delete_document(v)" class="fa fa-trash-o" title="Remove file" :filename="v.name" style="cursor: pointer; color:red;"></a>
                        </span>
                        <span v-else>
                            <i class="fa fa-info-circle" aria-hidden="true" title="Previously submitted documents cannot be deleted" style="cursor: pointer;"></i>
                        </span>
                    </p>
                </div>
                <span v-if="show_spinner"><i class='fa fa-2x fa-spinner fa-spin'></i></span>
            </div>
            <div v-if="!readonly" v-for="n in repeat">
                <div v-if="isRepeatable || (!isRepeatable && num_documents()==0)">
                    <input :name="name" type="file" class="form-control" :data-que="n" :accept="fileTypes" @change="handleChange" :required="isRequired"/>
                </div>
            </div>

        </div>
    </div>
</template>

<script>
import {
  api_endpoints,
  helpers
}
from '@/utils/hooks';
import CommentBlock from './comment_block.vue';
import HelpText from './help_text.vue';
import HelpTextUrl from './help_text_url.vue';
import { mapGetters } from 'vuex';
export default {
    props:{
        application_id: null,
        name:String,
        label:String,
        id:String,
        isRequired:String,
        help_text:String,
        field_data:Object,
        fileTypes:{
            default:function () {
                var file_types = 
                    "image/*," + 
                    "video/*," +
                    "audio/*," +
                    "application/pdf,text/csv,application/msword,application/vnd.ms-excel,application/x-msaccess," +
                    "application/x-7z-compressed,application/x-bzip,application/x-bzip2,application/zip," + 
                    ".dbf,.gdb,.gpx,.prj,.shp,.shx," + 
                    ".json,.kml,.gpx";
                return file_types;
            }
        },
        isRepeatable:Boolean,
        readonly:Boolean,
        docsUrl: String,
        help_text_url: String,
        isTableField: Boolean
    },
    components: {CommentBlock, HelpText, HelpTextUrl},
    data:function(){
        return {
            repeat:1,
            files:[],
            show_spinner: false,
            documents:[],
            filename:null,
        }
    },
    computed: {
        csrf_token: function() {
            return helpers.getCookie('csrftoken')
        },
        application_document_action: function() {
          return (this.application_id) ? `/api/application/${this.application_id}/process_document/` : '';
        },
        value: function() {
            return this.field_data.value;
        },
        getClass: function (){
            const file_class = this.isTableField ? "file-class" : "";
            return file_class;
        }
    },

    methods:{
        handleChange:function (e) {
            let vm = this;

            vm.show_spinner = true;
            if (vm.isRepeatable) {
                let  el = $(e.target).attr('data-que');
                let avail = $('input[name='+e.target.name+']');
                // Extracting text from a DOM node and interpreting it as HTML 
                // can lead to a XSS vulnerability when resolving avail list.
                // avail = [...avail.map(id => {
                //     return $(avail[id]).attr('data-que');
                // })];
                // reinterpreted (below)
                let avail_map = $('input[name='+e.target.name+']');
                avail = []
                $.map(avail_map, function(val, i) {
                    avail.push($(avail_map[i]).attr('data-que'))
                });

                avail.pop();
                if (vm.repeat == 1) {
                    vm.repeat+=1;
                }else {
                    if (avail.indexOf(el) < 0 ){
                        vm.repeat+=1;
                    }
                }
                $(e.target).css({ 'display': 'none'});

            } else {
                vm.files = [];
            }
            vm.files.push(e.target.files[0]);

            if (e.target.files.length > 0) {
                //vm.upload_file(e)
                vm.save_document(e);
            }

            vm.show_spinner = false;
        },
        truncatedName: function (name){
            if(name.length > 10){
                return name.substring(0, 6) + '...';
            }
            else{
                return name;
            }
        },

        /*
        upload_file: function(e) {
            let vm = this;
            $("[id=save_and_continue_btn][value='Save Without Confirmation']").trigger( "click" );
        },
		*/

        get_documents: function() {
            let vm = this;

            var formData = new FormData();
            formData.append('action', 'list');
            formData.append('input_name', vm.name);
            formData.append('csrfmiddlewaretoken', vm.csrf_token);
            vm.$http.post(vm.application_document_action, formData)
                .then(res=>{
                    vm.documents = res.body;
                    //console.log(vm.documents);
                    vm.show_spinner = false;
                });

        },

        delete_document: function(file) {
            let vm = this;
            vm.show_spinner = true;

            var formData = new FormData();
            formData.append('action', 'delete');
            formData.append('document_id', file.id);
            formData.append('csrfmiddlewaretoken', vm.csrf_token);

            vm.$http.post(vm.application_document_action, formData)
                .then(res=>{
                    vm.documents = vm.get_documents()
                    //vm.documents = res.body;
                    vm.show_spinner = false;
                });

        },
        
        uploadFile(e){
            let vm = this;
            let _file = null;

            if (e.target.files && e.target.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(e.target.files[0]); 
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = e.target.files[0];
            }
            return _file
        },

        save_document: function(e) {
            let vm = this; 

            var formData = new FormData();
            formData.append('action', 'save');
            formData.append('application_id', vm.application_id);
            formData.append('input_name', vm.name);
            formData.append('filename', e.target.files[0].name);
            formData.append('_file', vm.uploadFile(e));
            formData.append('csrfmiddlewaretoken', vm.csrf_token);

            vm.$http.post(vm.application_document_action, formData)
                .then(res=>{
                    vm.documents = res.body;
                },err=>{
                });

        },

        num_documents: function() {
            let vm = this;
            if (vm.documents) {
                return vm.documents.length;
            }
            return 0;
        },
    },
    mounted:function () {
        let vm = this;
        vm.documents = vm.get_documents();
        if (vm.value) {
            //vm.files = (Array.isArray(vm.value))? vm.value : [vm.value];
            if (Array.isArray(vm.value)) {
                vm.value;
            } else {
                var file_names = vm.value.replace(/ /g,'_').split(",")
                vm.files = file_names.map(function( file_name ) { 
                      return {name: file_name}; 
                });
            }
        }
    }
}

</script>

<style lang="css">
    input {
        box-shadow:none;
    }
.file-class {
    margin-top: -20px;
}
</style>
