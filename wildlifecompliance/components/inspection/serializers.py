import traceback

from rest_framework.fields import CharField
from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeometryField

from ledger.accounts.models import EmailUser, Address
from wildlifecompliance.components.inspection.models import (
    Inspection,
    InspectionUserAction,
    InspectionCommsLogEntry,
    InspectionType,
    )
from wildlifecompliance.components.main.models import get_related_items
from wildlifecompliance.components.main.serializers import CommunicationLogEntrySerializer
from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    CompliancePermissionGroupMembersSerializer
)
from rest_framework import serializers
from django.core.exceptions import ValidationError
from wildlifecompliance.components.main.fields import CustomChoiceField

from wildlifecompliance.components.users.serializers import (
    ComplianceUserDetailsOptimisedSerializer,
    CompliancePermissionGroupMembersSerializer,
    UserAddressSerializer,
)


class InspectionTypeSerializer(serializers.ModelSerializer):
   class Meta:
       model = InspectionType
       fields = '__all__'


class InspectionSerializer(serializers.ModelSerializer):
    allocated_group = serializers.SerializerMethodField()
    user_in_group = serializers.SerializerMethodField()
    can_user_action = serializers.SerializerMethodField()
    user_is_assignee = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    #inspection_type = InspectionTypeSerializer()

    class Meta:
        model = Inspection
        fields = (
                'id',
                'number',
                'status',
                'title',
                'details',
                'planned_for_date',
                'planned_for_time',
                'party_inspected',
                'assigned_to_id',
                'allocated_group',
                'allocated_group_id',
                'user_in_group',
                'can_user_action',
                'user_is_assignee',
                'inspection_type_id',
                )
        read_only_fields = (
                'id',
                )

    def get_user_in_group(self, obj):
        user_id = self.context.get('request', {}).user.id

        if obj.allocated_group:
           for member in obj.allocated_group.members:
               if user_id == member.id:
                  return True
        
        return False

    def get_can_user_action(self, obj):
        user_id = self.context.get('request', {}).user.id

        if user_id == obj.assigned_to_id:
            return True
        elif obj.allocated_group and not obj.assigned_to_id:
           for member in obj.allocated_group.members:
               if user_id == member.id:
                  return True
        
        return False

    def get_user_is_assignee(self, obj):
        user_id = self.context.get('request', {}).user.id
        if user_id == obj.assigned_to_id:
            return True

        return False

    def get_allocated_group(self, obj):
        allocated_group = [{
            'email': '',
            'first_name': '',
            'full_name': '',
            'id': None,
            'last_name': '',
            'title': '',
            }]
        returned_allocated_group = CompliancePermissionGroupMembersSerializer(instance=obj.allocated_group)
        for member in returned_allocated_group.data['members']:
            allocated_group.append(member)

        return allocated_group


class SaveInspectionSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    allocated_group_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    inspection_type_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    
    class Meta:
        model = Inspection
        fields = (
                'id',
                'title',
                'details',
                'planned_for_date',
                'planned_for_time',
                'party_inspected',
                'assigned_to_id',
                'allocated_group_id',
                'inspection_type_id'
                )
        read_only_fields = (
                'id',
                )

#class SaveInspectionSerializer(serializers.ModelSerializer):
 #   title = models.CharField(max_length=200, blank=True, null=True)
  #  details = models.TextField(blank=True, null=True)
   # number = models.CharField(max_length=50, blank=True, null=True)
    #planned_for_date = models.DateField(null=True)
    #planned_for_time = models.CharField(max_length=20, blank=True, null=True)



class InspectionUserActionSerializer(serializers.ModelSerializer):
    who = serializers.CharField(source='who.get_full_name')

    class Meta:
        model = InspectionUserAction
        fields = '__all__'


class InspectionCommsLogEntrySerializer(CommunicationLogEntrySerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = InspectionCommsLogEntry
        fields = '__all__'
        read_only_fields = (
            'customer',
        )

    def get_documents(self, obj):
        return [[d.name, d._file.url] for d in obj.documents.all()]


class InspectionDatatableSerializer(serializers.ModelSerializer):
    user_action = serializers.SerializerMethodField()
    inspection_type = InspectionTypeSerializer()
    planned_for = serializers.SerializerMethodField()
    status = CustomChoiceField(read_only=True)
    
    class Meta:
        model = Inspection
        fields = (
                'number',
                'title',
                'inspection_type',
                'status',
                'planned_for',
                'user_action',
                )

    # def get_user_action(self, obj):
    #     process_url = '<a href=/internal/inspection/' + str(obj.id) + '>Process</a>'
    #     return process_url

    def get_user_action(self, obj):
        user_id = self.context.get('request', {}).user.id
        view_url = '<a href=/internal/inspection/' + str(obj.id) + '>View</a>'
        process_url = '<a href=/internal/inspection/' + str(obj.id) + '>Process</a>'
        returned_url = ''

        if obj.status == 'closed':
            returned_url = view_url
        elif user_id == obj.assigned_to_id:
            returned_url = process_url
        elif (obj.allocated_group
                and not obj.assigned_to_id):
            for member in obj.allocated_group.members:
                if user_id == member.id:
                    returned_url = process_url

        if not returned_url:
            returned_url = view_url

        return returned_url

    def get_planned_for(self, obj):
        if obj.planned_for_date:
            if obj.planned_for_time:
                return obj.planned_for_date.strftime("%d/%m/%Y") + '  ' + obj.planned_for_time.strftime('%H:%M')
            else:
                return obj.planned_for_date.strftime("%d/%m/%Y")
        else:
            return None

class UpdateAssignedToIdSerializer(serializers.ModelSerializer):
    assigned_to_id = serializers.IntegerField(
        required=False, write_only=True, allow_null=True)
    
    class Meta:
        model = Inspection
        fields = (
            'assigned_to_id',
        )

