<template lang="html">
    <div>
        <!-- <div v-if="canViewComments" class="inline-block"> -->
            <div v-if="canViewComments && canEditOfficerComments" class="inline-block">
                <div v-if="!showingComment(COMMENT_TYPE_OFFICER)">
                    <a v-if="field_data.officer_comment" href="" @click.prevent="toggleComment(COMMENT_TYPE_OFFICER)" title="Officer Comments"><i style="color:red" class="fa fa-comment-o">&nbsp;</i></a>
                    <a v-else href="" @click.prevent="toggleComment(COMMENT_TYPE_OFFICER)" title="Officer Comments"><i class="fa fa-comment-o">&nbsp;</i></a>
                </div>
                <a href="" v-else @click.prevent="toggleComment(COMMENT_TYPE_OFFICER)"><i class="fa fa-ban">&nbsp;</i></a>
            </div>
            <div v-if="canViewComments && !canEditOfficerComments && field_data.officer_comment" style="color:red" class="inline-block">
                <i class="fa fa-comment-o">&nbsp;</i>
                <span>{{field_data.officer_comment}}</span>
            </div>                
        <!-- </div> -->

        <!-- <div v-if="canViewDeficiencies" class="inline-block"> -->
            <div v-if="canViewDeficiencies && canEditDeficiencies" class="inline-block">
                <div v-if="!showingComment(COMMENT_TYPE_DEFICIENCY)">
                    <a v-if="field_data.deficiency_value" href=""  @click.prevent="toggleComment(COMMENT_TYPE_DEFICIENCY)"><i style="color:red" class="fa fa-exclamation-triangle" title="Deficiencies">&nbsp;</i></a>
                    <a v-else href="" @click.prevent="toggleComment(COMMENT_TYPE_DEFICIENCY)" title="Deficiencies"><i class="fa fa-exclamation-triangle">&nbsp;</i></a>
                </div>
                <a href="" v-else @click.prevent="toggleComment(COMMENT_TYPE_DEFICIENCY)"><i class="fa fa-ban">&nbsp;</i></a>
            </div>
            <div v-if="canViewDeficiencies && !canEditDeficiencies && field_data.deficiency_value" style="color:red" class="inline-block">
                <i class="fa fa-exclamation-triangle">&nbsp;</i>
                <span>{{field_data.deficiency_value}}</span>
            </div>
        <!-- </div> -->

        <!-- <div v-if="canViewComments" class="inline-block"> -->
            <div v-if="canViewComments && canEditAssessorComments" class="inline-block">
                <div v-if="!showingComment(COMMENT_TYPE_ASSESSOR)">
                    <a v-if="field_data.assessor_comment" href="" @click.prevent="toggleComment(COMMENT_TYPE_ASSESSOR)"><i style="color:red" class="fa fa-clipboard" title="Assessor Comments">&nbsp;</i></a>
                    <a v-else href="" @click.prevent="toggleComment(COMMENT_TYPE_ASSESSOR)" title="Assessor Comments"><i class="fa fa-clipboard">&nbsp;</i></a>
                </div>
                <a href="" v-else @click.prevent="toggleComment(COMMENT_TYPE_ASSESSOR)"><i class="fa fa-ban">&nbsp;</i></a>
            </div>
            <div v-else-if="canViewComments && field_data.assessor_comment" style="color:red" class="inline-block">
                <i class="fa fa-clipboard">&nbsp;</i>
                <span>{{field_data.assessor_comment}}</span>
            </div>    
        <!-- </div> -->

        <Comment :question="label ? label : name" :name="name+'-officer-comment-field'" v-show="showingComment(COMMENT_TYPE_OFFICER)" :field_data="field_data" :commentType="COMMENT_TYPE_OFFICER"/>
        <Comment :question="label ? label : name" :name="name+'-assessor-comment-field'" v-show="showingComment(COMMENT_TYPE_ASSESSOR)" :field_data="field_data" :commentType="COMMENT_TYPE_ASSESSOR"/>
        <Comment :question="label ? label : name" :name="name+'-deficiency-field'" v-show="showingComment(COMMENT_TYPE_DEFICIENCY)" :field_data="field_data" :commentType="COMMENT_TYPE_DEFICIENCY"/>
    </div>
</template>

<script>
import '@/scss/forms/form.scss';

import {
    COMMENT_TYPE_OFFICER,
    COMMENT_TYPE_ASSESSOR,
    COMMENT_TYPE_DEFICIENCY,
} from '@/store/constants';

import Comment from './comment.vue';
import { mapGetters } from 'vuex';

const CommentBlock = {
    props:{
        label: {
            type: String | null,
            required: true,
        },
        name: {
            type: String,
            required: true,
        },
        field_data: {
            type: Object | null,
            required: true,
        },
    },
    components: {
        Comment,
    },
    data(){
        return {
            showingCommentTypes: {
                [COMMENT_TYPE_OFFICER]: false,
                [COMMENT_TYPE_ASSESSOR]: false,
                [COMMENT_TYPE_DEFICIENCY]: false,
            },
            COMMENT_TYPE_OFFICER: COMMENT_TYPE_OFFICER,
            COMMENT_TYPE_ASSESSOR: COMMENT_TYPE_ASSESSOR,
            COMMENT_TYPE_DEFICIENCY: COMMENT_TYPE_DEFICIENCY,
        };
    },
    methods: {
        showingComment: function(comment_type) {
            return this.showingCommentTypes[comment_type];
        },
    },
    computed:{
        ...mapGetters([
            'canViewComments',
            'canViewDeficiencies',
            'canEditDeficiencies',
            'selected_activity_tab_id',
            'canAssignOfficerFor',
            'canAssignAssessorFor',
        ]),
        toggleComment: function(){
            return (comment_type) => {
                this.showingCommentTypes[comment_type] = !this.showingCommentTypes[comment_type];
            }
        },
        canEditOfficerComments: function() {
            // return this.canAssignOfficerFor(this.selected_activity_tab_id);
            return this.canEditDeficiencies
        },
        canEditAssessorComments: function() {
            return this.canAssignAssessorFor(this.selected_activity_tab_id);
        },
    }
}

export default CommentBlock;
</script>
