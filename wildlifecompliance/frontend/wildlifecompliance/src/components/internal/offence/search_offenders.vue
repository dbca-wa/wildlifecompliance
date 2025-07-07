<template lang="html">
    <div class="">
        <div class="col-sm-12 form-group"><div class="row">
                <div v-if="showSearchOffender" class="alert alert-info">Search existing offender records or create new offender record.</div>
                <label v-if="showSearchOffender" class="col-sm-4">Search offender</label>
        </div></div>
        <div class="form-group"><div class="row">
            <div class="col-sm-12">
                <div v-if="showSearchOffender" class="col-sm-9">
                    <input :id="elemId" :class="classNames" :readonly="!isEditable" ref="search_offender"/>
                </div>
                <div v-if="showCreateNewOffender" class="col-sm-2">
                    <input :disabled="!isEditable" type="button" class="btn btn-primary" value="Create New Offender" @click.prevent="createNewOffender()" />
                </div>

                <div v-if="displayCreateOffender">
                    <input type="button" class="btn btn-primary" value="Back" @click.prevent="CancelNewOffender()" />
                    <SearchPersonOrganisation
                    :excludeStaff="true"
                    :personOnly="true"
                    classNames="form-control"
                    @entity-selected="entitySelected"
                    showCreateUpdate
                    :allowCreateEdit="true"
                    :allowSaveUser="false"
                    :emailRequired="false"
                    :info="'Search for offenders among ledger user accounts or create a new offender.'"
                    ref="search_users"
                    domIdHelper="offender"
                    v-bind:key="updateSearchPersonOrganisationBindId"/>
                </div>
            </div>
        </div></div>
    </div>
</template>

<script>
import Awesomplete from "awesomplete";
import $ from "jquery";
import "bootstrap/dist/css/bootstrap.css";
import "awesomplete/awesomplete.css";
import hash from 'object-hash';
import SearchPersonOrganisation from "@common-components/search_person_or_organisation.vue";

export default {
    name: "search-offender",
    data: function(){
        let vm = this
        vm.awesomplete_obj = null;
        return {
            entity: {
                id: null,
                data_type: null,
                full_name: null,
                source: null,
            },
            searchType: '',
            errorText: '',
            uuid: 0,
            showCreateNewOffender: false,
            displayCreateOffender: false,
            showSearchOffender: true,
        }
    },
    components: {
        SearchPersonOrganisation,
    },
    watch: {
        entity: {
            handler: function (){
                if (this.entity.id) {
                    this.$emit('entity-selected', {
                        id: this.entity.id,
                        data_type: this.entity.data_type,
                        full_name: this.entity.full_name,
                        source: this.entity.source,
                    });
                }
            },
            deep: true
        },
    },
    computed: {
        updateSearchPersonOrganisationBindId: function() {
            this.uuid += 1
            return 'offender' + this.uuid
        },
        elemId: function() {
            this.uuid += 1
            let domId = this.uuid + 'search';

            if (this.domIdHelper) {
                domId += this.domIdHelper;
            }
            return domId;
        },
    },
    props: {
        classNames: {
            required: false,
            default: 'form-control',
        },
        maxItems: {
            required: false,
            default: 10
        },
        isEditable: {
            required: false,
            default: true
        },
        domIdHelper: {
            type: String,
            required: false,
        },
    },
    methods: {
        entitySelected: function(para) {
            this.entity = {
                id: para.id,
                data_type: para.data_type,
                full_name: para.full_name,
                source: 'email_users',
            }
        },
        CancelNewOffender: function() {
            this.displayCreateOffender = false;
            this.showCreateNewOffender = true;
            this.showSearchOffender = true;
            this.creatingPerson = false;
            this.uuid += 1;
            this.$nextTick(()=>{
                this.initAwesomplete();
            });
            this.object_hash = hash(this.entity);
            let element_search = $('#' + this.elemId);
            element_search.val('');
        },
        clearPerson: function() {
            this.$emit('clear-person');
            this.entity = {
                'id': 0, 
                'data_type': 'individual',
                'full_name': '',
                'source': '',
            };
            let element_search = $('#' + this.elemId);
            element_search.val('');
            this.displayCreateOffender = false;
        },
        createNewOffender: function() {
            this.creatingPerson = true;
            this.clearPerson();
            this.$nextTick(() => {
                this.displayCreateOffender = true;
                this.showCreateNewOffender = false;
                this.showSearchOffender = false;
                this.setInput('');
            });
        },
        clearInput: function(){
            if (this.showSearchOffender) {
                document.getElementById(this.elemId).value = "";
            }
            if (this.displayCreateOffender) {
                this.$refs.search_users.clearInput();
            }
        },
        setInput: function(str){
            if (this.showSearchOffender) {
                document.getElementById(this.elemId).value = str;
            }
        },
        markMatchedText(original_text, input) {
            try {
                let ret_text = original_text.replace(new RegExp(input, "gi"), function( a, b) {
                    return "<mark>" + a + "</mark>";
                });
                return ret_text;
            } catch {
                return ""
            }
        },
        initAwesomplete: function() {
            let vm = this;

            let element_search = document.getElementById(vm.elemId);
            vm.awesomplete_obj = new Awesomplete(element_search, {
                maxItems: vm.maxItems,
                sort: false,
                filter: () => {
                    return true;
                }, 
                item: function(text, input) {
                    let ret = Awesomplete.ITEM(text, ""); // Not sure how this works but this doesn't add <mark></mark>
                    return ret;
                },
                data: function(item, input) {
                    let f_name = item.first_name ? item.first_name : "";
                    let l_name = item.last_name ? item.last_name : "";
        
                    let full_name = [f_name, l_name].filter(Boolean).join(" ");
                    let email = item.email ? "E:" + item.email : "";
                    let p_number = item.phone_number ? "P:" + item.phone_number : "";
                    let m_number = item.mobile_number ? "M:" + item.mobile_number : "";
                    let dob = item.dob ? "DOB:" + item.dob : "DOB: ---";
        
                    let full_name_marked = "<strong>" + vm.markMatchedText(full_name, input) + "</strong>";
                    let email_marked = vm.markMatchedText(email, input);
                    let p_number_marked = vm.markMatchedText(p_number, input);
                    let m_number_marked = vm.markMatchedText(m_number, input);
                    let dob_marked = vm.markMatchedText(dob, input);
        
                    let myLabel = [
                        full_name_marked,
                        email_marked,
                        p_number_marked,
                        m_number_marked,
                        dob_marked
                    ].filter(Boolean).join("<br />");
                    myLabel = "<div data-item-id=" + item.id + ' data-full-name="' + full_name + '" data-type="individual">' + myLabel + "</div>";
        
                    return {
                        label: myLabel, // Displayed in the list below the search box
                        value: [full_name, dob].filter(Boolean).join(", "), // Inserted into the search box once selected
                        id: item.id
                    };
                }
            });
            $(element_search)
            .on("keyup", function(ev) {
                var keyCode = ev.keyCode || ev.which;
                if ((48 <= keyCode && keyCode <= 90) || (96 <= keyCode && keyCode <= 105) || keyCode == 8 || keyCode == 46) {
                    vm.search_offender(ev.target.value);
                    return false;
                }
            })
            .on("awesomplete-selectcomplete", function(ev) {
                ev.preventDefault();
                ev.stopPropagation();
                return false;
            })
            .on("awesomplete-select", function(ev) {
                let origin = $(ev.originalEvent.origin);
                let originTagName = origin[0].tagName;
                switch(originTagName){
                    case "STRONG":
                        origin = origin.parent();
                        break;
                    case "MARK":
                        origin = origin.parent().parent();
                        break;
                    case "LI":
                        origin = origin.children().first();
                        break;
                }
                let data_item_id = origin[0].getAttribute("data-item-id");
                let data_type = origin[0].getAttribute("data-type");
                let data_full_name = origin[0].getAttribute("data-full-name");

                vm.$nextTick(() => {
                    let data_item_id_int = parseInt(data_item_id);
                    vm.entity = {
                        'id': data_item_id_int, 
                        'data_type': data_type,
                        'full_name': data_full_name,
                        'source': 'offenders',
                    };
                });
            });
        },
        search_offender(searchTerm){
            var vm = this;
            let suggest_list_offender = [];
            suggest_list_offender.length = 0;
            vm.awesomplete_obj.list = [];

            /* Cancel all the previous requests */
            if (vm.ajax_for_offender != null) {
                vm.ajax_for_offender.abort();
                vm.ajax_for_offender = null;
            }

            let search_url = "/api/search_offender/?search=";

            vm.ajax_for_offender = $.ajax({
                type: "GET",
                url: search_url + searchTerm,
                success: function(data) {
                    if (data && data.results) {
                        let persons = data.results;
                        let limit = Math.min(vm.maxItems, persons.length);
                        for (var i = 0; i < limit; i++) {
                        suggest_list_offender.push(persons[i]);
                        }
                    }
                    vm.awesomplete_obj.list = suggest_list_offender;
                    vm.awesomplete_obj.evaluate();
                    // show 'Create' buttons
                    if (searchTerm.length >=2) {
                        vm.showCreateNewOffender = true;
                    }
                },
                error: function(e) {}
            });
        },
    },
    created: async function() {
        this.uuid += 1;
        this.$nextTick(()=>{
            this.initAwesomplete();
        });
        this.object_hash = hash(this.entity);
    },
}
</script>

<style>
.awesomplete > ul {
    margin-top: 0 !important;
    z-index: 10000;
}
.awesomplete > ul > li {
    border-bottom: 1px solid lightgray;
    margin: 5px 10px 5px 10px;
}
</style>
