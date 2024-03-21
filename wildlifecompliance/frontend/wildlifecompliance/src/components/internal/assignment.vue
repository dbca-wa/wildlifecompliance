<template id="assignment">
    <div>
        <div> <!--v-if="allocatedGroup" class="form-group">-->
            <div class="row">
            <div class="col-sm-12 top-buffer-s">
                <strong>Currently assigned to</strong><br/>
            </div>
            </div>
            <div class="row">
                <div class="col-sm-9">
                <select :disabled="!user_in_group" class="form-control" v-model="assigned_to_id" @change="updateAssignedToId()">
                <option  v-for="option in allocated_group" :value="option.id" v-bind:key="option.id" :selected="option.id==assigned_to_id">
                    {{ option.full_name }}
                </option>
                </select>
                </div>
            </div>
        </div>
        <div v-if="user_in_group && !user_is_assignee">
            <a @click="updateAssignedToId('current_user')" class="btn pull-right">
                Assign to me
            </a>
        </div>
    </div>
</template>
<script>
import Vue from "vue";
import { api_endpoints, helpers } from "@/utils/hooks";
export default {
    name: 'Assignment',
    props: {
        user_in_group:{
            type: Boolean,
            required: true
        },
        user_is_assignee:{
            type: Boolean,
            required: true
        },
        assigned_to_id:{
            type: String,
            required: false
        },
        allocated_group_id:{
            type: String,
            required: false
        },
        assign_url:{
            type: String,
            required: true
        },
    },
    data: function() {
        let vm = this;
        return {
            allocated_group: this.getAllocatedGroup(this.allocated_group_id),
        }         
    },
    components:{
    },
    computed: {       
    },
    methods:{
        updateAssignedToId: async function (user) {
            let url = this.assign_url;
            let payload = null;
            if (user === 'current_user' && this.user_in_group) {
                payload = {'current_user': true};
            } else if (user === 'blank') {
                payload = {'blank': true};
            } else {
                payload = { 'assigned_to_id': this.assigned_to_id };
            }
            let res = await Vue.http.post(
                url,
                payload
            );
            this.$emit('update-assigned-to-id', res.body);
        },
        getAllocatedGroup: async function(id) {
            Vue.set(this, 'allocated_group', []);
            let allocatedGroupResponse = await Vue.http.post(
            api_endpoints.allocated_group_members,
            {
                'id': id,
            });
            if (allocatedGroupResponse.ok) {
                Vue.set(this, 'allocated_group', allocatedGroupResponse.body);
            } 
        },        
    },
    watch: 
    {
        allocated_group_id(after,before) {
            if (before === undefined && after !== undefined) {
                console.log("ALLOCATED GROUP ID:"+this.allocated_group_id);
                this.getAllocatedGroup(this.allocated_group_id);
            }
        }
    },
}
</script>
