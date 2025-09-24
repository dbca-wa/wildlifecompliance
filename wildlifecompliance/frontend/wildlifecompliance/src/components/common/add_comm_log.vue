<template lang="html">
    <div id="AddComms">
        <bootstrapModal 
            :modelValue="modelValue"
            @update:modelValue="$emit('update:modelValue', $event)"
            title="Communication log - Add entry" 
            size="lg"
            ok-text="Add"
            @submit="ok()" 
            @close="cancel()"
        >
            <div class="container-fluid">
                <div class="row">
                    <form class="form-horizontal" name="commsForm">
                        <alert v-if="showError" type="danger"><strong>{{errorString}}</strong></alert>
                        <div class="col-sm-12">
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label float-start"  for="Name">To</label>
                                    </div>
                                    <div class="col-sm-4">
                                        <input type="text" class="form-control" name="to" v-model="to">
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label float-start"  for="Name">From</label>
                                    </div>
                                    <div class="col-sm-4">
                                        <input type="text" class="form-control" name="fromm" v-model="from">
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label float-start"  for="Name">Type</label>
                                    </div>
                                    <div class="col-sm-4">
                                        <select class="form-control" name="type" v-model="log_type">
                                            <option value="">Select Type</option>
                                            <option value="email">Email</option>
                                            <option value="file_note">File Note</option>
                                            <option value="mail">Mail</option>
                                            <option value="phone">Phone</option>
                                            <option value="person">Person</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label float-start"  for="Name">Subject/Description</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <input type="text" class="form-control" name="subject" style="width:70%;" v-model="subject">
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label float-start"  for="Name">Text</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <textarea name="text" class="form-control" style="width:70%;" v-model="text"></textarea>
                                    </div>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="row">
                                    <div class="col-sm-3">
                                        <label class="control-label float-start"  for="Name">Attachments</label>
                                    </div>
                                    <div class="col-sm-9">
                                        <template v-for="(f,i) in files">
                                            <div :class="'row top-buffer file-row-'+i">
                                                <div class="col-sm-4">
                                                    <span v-if="f.file == null" class="btn btn-info btn-file float-start">
                                                        Attach File <input type="file" :name="'file-upload-'+i" :class="'file-upload-'+i" @change="uploadFile('file-upload-'+i,f)"/>
                                                    </span>
                                                    <span v-else class="btn btn-info btn-file float-start">
                                                        Update File <input type="file" :name="'file-upload-'+i" :class="'file-upload-'+i" @change="uploadFile('file-upload-'+i,f)"/>
                                                    </span>
                                                </div>
                                                <div class="col-sm-4">
                                                    <span>{{f.name}}</span>
                                                </div>
                                                <div class="col-sm-4">
                                                    <button @click="removeFile(i)" class="btn btn-danger">Remove</button>
                                                </div>
                                            </div>
                                        </template>
                                        <a href="" @click.prevent="attachAnother"><i class="fa fa-lg fa-plus top-buffer-2x"></i></a>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
            </div>
            <!-- <div slot="footer">
                <button type="button" v-if="addingComms" disabled class="btn btn-default" @click="ok"><i class="fa fa-spinner fa-spin"></i> Adding</button>
                <button type="button" v-else class="btn btn-default" @click="ok">Add</button>
                <button type="button" class="btn btn-default" @click="cancel">Cancel</button>
            </div> -->
            <template #footer>
                <button type="button" v-if="addingComms" disabled class="btn btn-secondary"><i class="fa fa-spinner fa-spin"></i> Adding</button>
                <button type="button" v-else class="btn btn-primary" @click="ok">Add</button>
                <button type="button" class="btn btn-secondary" @click="cancel">Cancel</button>
            </template>
        </bootstrapModal>
    </div>
</template>

<script>
// import bootstrapModal from '@vue-utils/bootstrap-modal.vue'
import bootstrapModal from '@vue-utils/bootstrap5-modal.vue'
import alert from '@vue-utils/alert.vue'
import { helpers, fetch_util } from "@/utils/hooks.js"
export default {
    name:'Add-Comms',
    compatConfig: {
        COMPONENT_V_MODEL: false
    },
    components:{
        bootstrapModal,
        alert
    },
    props:{
        modelValue: {
            type: Boolean,
            required: true,
        },
        url: {
            type: String,
            required: true
        }
    },
    emits: ['update:modelValue'],
    data:function () {
        let vm = this;
        return {
            // isModalOpen:false,
            form:null,
            comms: {},
            state: 'proposed_licence',
            addingComms: false,
            validation_form: null,
            errors: false,
            errorString: '',
            successString: '',
            success:false,
            datepickerOptions:{
                format: 'YYYY-MM-DD',
                showClear:true,
                useCurrent:false,
                keepInvalid:true,
                allowInputToggle:true
            },
            to: "",
            from: "",
            log_type: "",
            subject: "",
            text: "",
            /*files: [
                {
                    'file': null,
                    'name': ''
                }
            ]*/
           files: [],
        }
    },
    computed: {
        showError: function() {
            var vm = this;
            return vm.errors;
        },
    },
    methods:{
        ok:function () {
            let vm =this;
            if($(vm.form).valid()){
                vm.sendData();
            }
        },
        uploadFile(target,file_obj){
            let vm = this;
            let _file = null;
            var input = $('.'+target)[0];
            if (input.files && input.files[0]) {
                var reader = new FileReader();
                reader.readAsDataURL(input.files[0]); 
                reader.onload = function(e) {
                    _file = e.target.result;
                };
                _file = input.files[0];
            }
            file_obj.file = _file;
            file_obj.name = _file.name;
        },
        removeFile(index){
            let length = this.files.length;
            $('.file-row-'+index).remove();
            this.files.splice(index,1);
            this.$nextTick(() => {
                length == 1 ? this.attachAnother() : '';
            });
        },
        attachAnother(){
            this.files.push({
                'file': null,
                'name': ''
            })
        },
        cancel:function () {
            this.close()
        },
        close:function () {
            let vm = this;
            // this.isModalOpen = false;
            this.$emit('update:modelValue', false); 
            this.comms = {};
            this.errors = false;
            $('.has-error').removeClass('has-error');
            // this.validation_form.resetForm();
            if (this.validation_form) {
                this.validation_form.resetForm();
            }

            this.to = "";
            this.from = "";
            this.type = "";
            this.subject = "";
            this.text = "";

            let file_length = vm.files.length;
            this.files = [];
            for (var i = 0; i < file_length;i++){
                vm.$nextTick(() => {
                    $('.file-row-'+i).remove();
                });
            }
            this.attachAnother();
        },
        sendData:function(){
            let vm = this;
            vm.errors = false;
            let comms = new FormData(); 
            comms.append('to',this.to);
            comms.append('fromm',this.from);
            comms.append('type',this.log_type);
            comms.append('subject',this.subject);
            comms.append('text',this.text);
            comms.append('files',this.files);
            for (let i = 0; i < vm.files.length; i++) {
                comms.append('files', vm.files[i].file);
            }
            console.log(comms)
            vm.addingComms = true;
            let request = fetch_util.fetchUrl(vm.url,{method:'POST', body:comms},{})
            request.then((response)=>{
                    vm.addingComms = false;
                    vm.close();
                },(error)=>{
                    vm.errors = true;
                    vm.addingComms = false;
                    vm.errorString = helpers.apiVueResourceError(error);
                });
        },
        addFormValidations: function() {
            let vm = this;
            vm.validation_form = $(vm.form).validate({
                rules: {
                    to:"required",
                    fromm:"required",
                    type:"required",
                    subject:"required",
                    text:"required",
                },
                messages: {
                },
                showErrors: function(errorMap, errorList) {
                    $.each(this.validElements(), function(index, element) {
                        var $element = $(element);
                        $element.attr("data-original-title", "").parents('.form-group').removeClass('has-error');
                    });
                    // destroy tooltips on valid elements
                    $("." + this.settings.validClass).tooltip("destroy");
                    // add or update tooltips
                    for (var i = 0; i < errorList.length; i++) {
                        var error = errorList[i];
                        $(error.element)
                            .tooltip({
                                trigger: "focus"
                            })
                            .attr("data-original-title", error.message)
                            .parents('.form-group').addClass('has-error');
                    }
                }
            });
        },
    },
    mounted:function () {
            // let vm =this;
            // vm.form = document.forms.commsForm;
            // vm.addFormValidations();
    },
    watch: {
        modelValue(newValue) {
            if (newValue === true) {
                this.$nextTick(() => {
                    this.form = document.forms.commsForm;
                    this.addFormValidations();
                });
            }
        }
    },
}
</script>

<style lang="css">
.btn-file {
    position: relative;
    overflow: hidden;
}
.btn-file input[type=file] {
    position: absolute;
    top: 0;
    right: 0;
    min-width: 100%;
    min-height: 100%;
    font-size: 100px;
    text-align: right;
    filter: alpha(opacity=0);
    opacity: 0;
    outline: none;
    background: white;
    cursor: inherit;
    display: block;
}
.top-buffer{margin-top: 5px;}
.top-buffer-2x{margin-top: 10px;}
</style>
