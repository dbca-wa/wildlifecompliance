import json
from functools import reduce
from django.db.models import Q, Func, FloatField, Value
import operator
import traceback
import logging
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse
from django.core.exceptions import ValidationError
from wildlifecompliance import settings
from rest_framework import viewsets, serializers, status, mixins
from rest_framework.decorators import (
    action,
    renderer_classes,
)
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from datetime import datetime, timedelta
from django.urls import reverse
from django.shortcuts import redirect
from wildlifecompliance.components.main.api import save_location
from wildlifecompliance.components.main.models import ComplianceManagementSystemGroup,TemporaryDocumentCollection, ComplianceManagementSystemGroupPermission
from wildlifecompliance.components.main.process_document import (
        process_generic_document, 
        save_comms_log_document_obj
        )
from wildlifecompliance.components.main.email import prepare_mail
from wildlifecompliance.helpers import is_compliance_internal_user
from wildlifecompliance.components.inspection.models import (
    Inspection,
    InspectionUserAction,
    InspectionType,
    InspectionCommsLogEntry,
    InspectionFormDataRecord,
    )
from wildlifecompliance.components.call_email.models import (
        CallEmailUserAction,
        )
from wildlifecompliance.components.inspection.serializers import (
    InspectionSerializer,
    InspectionUserActionSerializer,
    InspectionCommsLogEntrySerializer,
    SaveInspectionSerializer,
    InspectionDatatableSerializer,
    UpdateAssignedToIdSerializer,
    InspectionTypeSerializer,
    EmailUserSerializer,
    InspectionTypeSchemaSerializer,
    InspectionOptimisedSerializer)
from wildlifecompliance.components.organisations.models import (
    Organisation,    
)
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from wildlifecompliance.components.inspection.email import send_mail
from django.db.models.functions import Concat
from django.db.models import Value

logger = logging.getLogger(__name__)

class InspectionFilterBackend(DatatablesFilterBackend):

    def filter_queryset(self, request, queryset, view):

        total_count = queryset.count()
        status_filter = request.GET.get('status_description')
        inspection_filter = request.GET.get('inspection_description')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        search_text = request.GET.get('search[value]')

        if search_text:
            search_text = search_text.lower()

            email_user_ids = list(EmailUser.objects.annotate(
                full_name=Concat(
                    'first_name',
                    Value(' '),
                    'last_name'
                ),
                legal_full_name=Concat(
                    'legal_first_name',
                    Value(' '),
                    'legal_last_name'
                ),
            ).filter(
                Q(email__icontains=search_text) |
                Q(first_name__icontains=search_text) |
                Q(last_name__icontains=search_text) |
                Q(full_name__icontains=search_text) |
                Q(legal_first_name__icontains=search_text) |
                Q(legal_last_name__icontains=search_text) |
                Q(legal_full_name__icontains=search_text) 
            ).values_list('id', flat=True))
            

            search_text_inspection_ids = list(Inspection.objects.filter(
                Q(number__icontains=search_text) |
                Q(status__icontains=search_text) |
                Q(inspection_type__inspection_type__icontains=search_text) |
                Q(title__icontains=search_text) |
                Q(assigned_to_id__in=email_user_ids) |
                Q(inspection_team_lead__in=email_user_ids)
            ).values_list('id', flat=True))

            queryset = queryset.filter(id__in=search_text_inspection_ids).distinct()

        status_filter = status_filter.lower() if status_filter else 'all'
        if status_filter != 'all':
            queryset = queryset.filter(status=status_filter)

        inspection_filter = inspection_filter.lower() if inspection_filter else 'all'
        if inspection_filter != 'all':
            queryset = queryset.filter(inspection_type__inspection_type__iexact=inspection_filter)

        if date_from:
            queryset = queryset.filter(planned_for_date__gte=date_from)
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            queryset = queryset.filter(planned_for_date__lte=date_to)
        
        fields = self.get_fields(request)
        ordering = self.get_ordering(request, view, fields)
        if len(ordering):
            for num, item in enumerate(ordering):
                if item == 'planned_for':
                    ordering[num] = 'planned_for_date'
                elif item == '-planned_for':
                    ordering[num] = '-planned_for_date'
                elif item == 'status__name':
                    ordering[num] = 'status'
                elif item == '-status__name':
                    ordering[num] = '-status'

            queryset = queryset.order_by(*ordering)

        setattr(view, '_datatables_total_count', total_count)
        return queryset


class InspectionPaginatedViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (InspectionFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    queryset = Inspection.objects.none()
    serializer_class = InspectionDatatableSerializer
    page_size = 10
    
    def get_queryset(self):
        if is_compliance_internal_user(self.request):
            return Inspection.objects.all()
        return Inspection.objects.none()

    @action(detail=False, methods=['GET', ])
    def get_paginated_datatable(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = InspectionDatatableSerializer(
            result_page, many=True, context={'request': request})
        return self.paginator.get_paginated_response(serializer.data)


class InspectionViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.RetrieveModelMixin):
    queryset = Inspection.objects.none()
    serializer_class = InspectionSerializer

    def get_queryset(self):
        if is_compliance_internal_user(self.request):
            return Inspection.objects.all()
        return Inspection.objects.none()

    @action(detail=False, methods=['GET', ])
    def datatable_list(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset()
            serializer = InspectionDatatableSerializer(
                qs, many=True, context={'request': request})
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=False, methods=['GET', ])    
    def status_choices(self, request, *args, **kwargs):
        res_obj = [] 
        for choice in Inspection.STATUS_CHOICES:
            res_obj.append({'id': choice[0], 'display': choice[1]});
        res_json = json.dumps(res_obj)
        return HttpResponse(res_json, content_type='application/json')
    
    @action(detail=True, methods=['GET', ])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = InspectionUserActionSerializer(qs, many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['GET', ])
    def comms_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.comms_logs.all()
            serializer = InspectionCommsLogEntrySerializer(qs, many=True)
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, instance=None, workflow=False, *args, **kwargs):
        try:
            with transaction.atomic():
                # create Inspection instance if not passed to this method
                if not instance:
                    instance = self.get_object()
                # add Inspection attribute to request_data
                request_data = request.data.copy()
                request_data['inspection'] = u'{}'.format(instance.id)
                if request_data.get('comms_log_id'):
                    comms = InspectionCommsLogEntry.objects.get(
                        id=request_data.get('comms_log_id')
                        )
                    serializer = InspectionCommsLogEntrySerializer(
                        instance=comms, 
                        data=request.data)
                else:
                    serializer = InspectionCommsLogEntrySerializer(
                        data=request_data
                        )
                serializer.is_valid(raise_exception=True)
                # overwrite comms with updated instance
                comms = serializer.save()
                # Save the files
                for f in request.FILES:
                    document = comms.documents.create()
                    document.name = str(request.FILES[f])
                    document._file = request.FILES[f]
                    document.save(path_to_file='wildlifecompliance/{}/{}/communications/{}/documents/'.format(
                    instance._meta.model_name, instance.id, comms.id,))
                # End Save Documents
                if workflow:
                    return comms
                else:
                    return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(e)
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['GET', ])
    @renderer_classes((JSONRenderer,))
    def get_inspection_team(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = EmailUserSerializer(
                instance.inspection_team.all(),
                context={
                    'inspection_team_lead_id': instance.inspection_team_lead_id
                },
                many=True)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def check_authorised_to_update(self,request,inspection_team_allowed=False):
        instance = self.get_object()
        user = self.request.user
        user_auth_groups = ComplianceManagementSystemGroupPermission.objects.filter(emailuser=user)

        if instance.assigned_to_id == user.id and user_auth_groups.filter(group__id__in=instance.allowed_groups).exists():
            return True
        elif inspection_team_allowed:
            return (user in instance.inspection_team.all() or user == instance.inspection_team_lead)
        else:
            return False
        
    def check_authorised_to_create(self,request):
        region_id = None if not request.data.get('region_id') else request.data.get('region_id')
        district_id = None if not request.data.get('district_id') else request.data.get('district_id')
        user = self.request.user
        #check that request user is an (inspection) officer or manager in the specified region and district
        if settings.AUTH_GROUP_REGION_DISTRICT_LOCK_ENABLED and settings.SUPER_AUTH_GROUPS_ENABLED and not ComplianceManagementSystemGroupPermission.objects.filter(
            Q(emailuser=user) & 
            (Q(group__region_id=region_id) | Q(group__region_id=None))
            ).filter(
                Q(group__name=settings.GROUP_INSPECTION_OFFICER) | 
                Q(group__name=settings.GROUP_MANAGER)).exists():
            return False
        elif settings.AUTH_GROUP_REGION_DISTRICT_LOCK_ENABLED and not ComplianceManagementSystemGroupPermission.objects.filter(
            emailuser=user, 
            group__region_id=region_id, 
            group__district_id=district_id
            ).filter(
                Q(group__name=settings.GROUP_INSPECTION_OFFICER) | 
                Q(group__name=settings.GROUP_MANAGER)).exists():
            return False
        elif not settings.AUTH_GROUP_REGION_DISTRICT_LOCK_ENABLED and not ComplianceManagementSystemGroupPermission.objects.filter(
                Q(emailuser=user) & 
                (Q(group__name=settings.GROUP_INSPECTION_OFFICER) | 
                Q(group__name=settings.GROUP_MANAGER))).exists():
            return False

        assigned_to_id = None if not request.data.get('assigned_to_id') else request.data.get('assigned_to_id')

        if settings.AUTH_GROUP_REGION_DISTRICT_LOCK_ENABLED and settings.SUPER_AUTH_GROUPS_ENABLED and not ComplianceManagementSystemGroupPermission.objects.filter(
            Q(emailuser=assigned_to_id) & 
            (Q(group__region_id=region_id) | Q(group__region_id=None))
            ).filter(
                Q(group__name=settings.GROUP_INSPECTION_OFFICER) | 
                Q(group__name=settings.GROUP_MANAGER)).exists():
            raise serializers.ValidationError(str("Specified user does not belong to appropriate authorisation group for the specified region/district"))
        elif settings.AUTH_GROUP_REGION_DISTRICT_LOCK_ENABLED and not ComplianceManagementSystemGroupPermission.objects.filter(
            emailuser=assigned_to_id, 
            group__region_id=region_id, 
            group__district_id=district_id
            ).filter(
                Q(group__name=settings.GROUP_INSPECTION_OFFICER) | 
                Q(group__name=settings.GROUP_MANAGER)).exists():
            raise serializers.ValidationError(str("Specified user does not belong to appropriate authorisation group for the specified region/district"))
        elif not settings.AUTH_GROUP_REGION_DISTRICT_LOCK_ENABLED and not ComplianceManagementSystemGroupPermission.objects.filter(
                Q(emailuser=assigned_to_id) & 
                (Q(group__name=settings.GROUP_INSPECTION_OFFICER) | 
                Q(group__name=settings.GROUP_MANAGER))).exists():
            raise serializers.ValidationError(str("Specified user does not belong to appropriate authorisation group for the specified region/district"))
        
        return True

    @action(detail=True, methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def modify_inspection_team(self, request, instance=None, workflow=False, user_id=None, new=False, *args, **kwargs):
        try:
            with transaction.atomic():

                if not new: #we do not need to check this for newly created inspections as it has already been checked
                    #check if user authorised to update - must be in allocated group and assigned
                    if not self.check_authorised_to_update(request):
                        return Response(
                            status=status.HTTP_401_UNAUTHORIZED,
                        )
                
                if not instance:
                    instance = self.get_object()
                if workflow:
                    action = 'add'
                    user_id = user_id
                else:
                    action = request.data.get('action') # 'add', 'remove or 'clear'
                    user_id = request.data.get('user_id')
                # ensure user_id is int
                if user_id:
                    user_id = int(user_id)

                if action and user_id:
                    user = EmailUser.objects.get(id=user_id)
                    team_member_list = instance.inspection_team.all()
                    if action == 'add':
                        if user not in team_member_list:
                            instance.inspection_team.add(user)
                            instance.log_user_action(
                                InspectionUserAction.ACTION_ADD_TEAM_MEMBER.format(
                                user.get_full_name()), request)
                        if not instance.inspection_team_lead or not team_member_list:
                           instance.inspection_team_lead = user
                           instance.log_user_action(
                               InspectionUserAction.ACTION_MAKE_TEAM_LEAD.format(
                               user.get_full_name()), request)
                    if action == 'remove':
                        if user in team_member_list:
                            instance.inspection_team.remove(user)
                            instance.log_user_action(
                                InspectionUserAction.ACTION_REMOVE_TEAM_MEMBER.format(
                                user.get_full_name()), request)
                        team_member_list = instance.inspection_team.all()
                        if team_member_list and not instance.inspection_team_lead_id in team_member_list:
                            instance.inspection_team_lead = team_member_list[0]
                        else:
                            instance.inspection_team_lead_id = None
                    if action == 'make_team_lead':
                        if user not in team_member_list:
                            instance.inspection_team.add(user)
                        instance.inspection_team_lead = user
                        instance.log_user_action(
                                InspectionUserAction.ACTION_MAKE_TEAM_LEAD.format(
                                user.get_full_name()), request)
                    instance.save()
                    if workflow:
                        return instance
                    else:
                        serializer = InspectionSerializer(instance, context={'request': request})
                        return Response(
                            serializer.data,
                            status=status.HTTP_201_CREATED,
                        )
                # List view - no modification
                else:
                    serializer = InspectionSerializer(instance, context={'request': request})
                    return Response(
                        serializer.data,
                        status=status.HTTP_200_OK,
                    )

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


    @action(detail=True, methods=['post'])
    @renderer_classes((JSONRenderer,))
    def form_data(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            InspectionFormDataRecord.process_form(
                request,
                instance,
                request.data.get('renderer_data'),
                action=InspectionFormDataRecord.ACTION_TYPE_ASSIGN_VALUE
            )
            return redirect(reverse('external'))
        
        except ValidationError as e:
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
        raise serializers.ValidationError(str(e))


    @action(detail=False, methods=['GET', ])
    def can_user_create(self, request, *args, **kwargs):
       # Find groups which has permissions determined above
       allowed_groups = ComplianceManagementSystemGroup.objects.filter(Q(name=settings.GROUP_INSPECTION_OFFICER)|Q(name=settings.GROUP_MANAGER))
       for allowed_group in allowed_groups:
           if request.user in allowed_group.get_members():
               return Response(True)
       return Response(False)

    @action(detail=False, methods=['GET', ])
    def optimised(self, request, *args, **kwargs):
        queryset = self.get_queryset().exclude(location__isnull=True)

        filter_inspection_type = request.query_params.get('inspection_type', '')
        filter_inspection_type = '' if filter_inspection_type.lower() == 'all' else filter_inspection_type
        filter_status = request.query_params.get('status', '')
        filter_status = '' if filter_status.lower() == 'all' else filter_status
        filter_date_from = request.query_params.get('date_from', '')
        filter_date_to = request.query_params.get('date_to', '')

        q_list = []
        if filter_inspection_type:
            q_list.append(Q(inspection_type__id=filter_inspection_type))
        if filter_status:
            q_list.append(Q(status__exact=filter_status))
        if filter_date_from:
            date_from = datetime.strptime(filter_date_from, '%d/%m/%Y')
            q_list.append(Q(planned_for_date__gte=date_from))
        if filter_date_to:
            date_to = datetime.strptime(filter_date_to, '%d/%m/%Y')
            q_list.append(Q(planned_for_date__lte=date_to))

        logger.info(q_list)

        queryset = queryset.filter(reduce(operator.and_, q_list)) if len(q_list) else queryset

        data = queryset.annotate(
            lat=Func("location__wkb_geometry", function="ST_Y", output_field=FloatField()),
            lon=Func("location__wkb_geometry", function="ST_X", output_field=FloatField()),
        ).values(
            'id',
            'lat',
            'lon',
        )
        return Response(data)


    #@action(detail=True, methods=['PUT', ])
    @renderer_classes((JSONRenderer,))
    #def inspection_save(self, request, workflow=False, *args, **kwargs):
    def update(self, request, workflow=False, *args, **kwargs):
        try:

            #check if user authorised to update - must be in allocated group and assigned OR on inspection team
            if not self.check_authorised_to_update(request, True):
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            
            with transaction.atomic():
                # 1. Save Location
                if (
                        request.data.get('location', {}).get('geometry', {}).get('coordinates', {}) or
                        request.data.get('location', {}).get('properties', {}).get('postcode', {}) or
                        request.data.get('location', {}).get('properties', {}).get('details', {})
                ):
                    location_request_data = request.data.get('location')
                    returned_location = save_location(location_request_data)
                    if returned_location:
                        request.data.update({'location_id': returned_location.get('id')})

                instance = self.get_object()
                # record individual inspected before update
                individual_inspected_id = instance.individual_inspected_id
                # record organisation inspected before update
                organisation_inspected_id = instance.organisation_inspected_id
                # record party_inspected before update
                party_inspected = instance.party_inspected
                if request.data.get('renderer_data'):
                    self.form_data(request)

                if instance.inspection_type and not request.data.get('inspection_type_id') and 'inspection_type_id' in request.data.keys():
                    del request.data['inspection_type_id']

                serializer = SaveInspectionSerializer(instance, data=request.data)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    serializer.save()
                    instance.log_user_action(
                            InspectionUserAction.ACTION_SAVE_INSPECTION_.format(
                            instance.number), request)
                    # Log individual_inspected update if applicable
                    if instance.party_inspected == 'individual' and individual_inspected_id and \
                            (individual_inspected_id != instance.individual_inspected_id or \
                            party_inspected != instance.party_inspected):
                        prev_individual_inspected = EmailUser.objects.get(id=individual_inspected_id)
                        instance.log_user_action(
                                InspectionUserAction.ACTION_CHANGE_INDIVIDUAL_INSPECTED.format(
                                prev_individual_inspected.get_full_name(),
                                instance.individual_inspected.get_full_name()), request)
                    # Log organisation_inspected update if applicable
                    if instance.party_inspected == 'organisation' and organisation_inspected_id and \
                            (organisation_inspected_id != instance.organisation_inspected_id or \
                            party_inspected != instance.party_inspected):
                        prev_organisation_inspected = Organisation.objects.get(id=organisation_inspected_id)
                        instance.log_user_action(
                                InspectionUserAction.ACTION_CHANGE_ORGANISATION_INSPECTED.format(
                                prev_organisation_inspected.name,
                                instance.organisation_inspected.name), request)

                    headers = self.get_success_headers(serializer.data)
                    return_serializer = InspectionSerializer(instance, context={'request': request})
                    return Response(
                            return_serializer.data,
                            status=status.HTTP_201_CREATED,
                            headers=headers
                            )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def update_assigned_to_id(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = None

            validation_serializer = InspectionSerializer(instance, context={'request': request})
            user_in_group = validation_serializer.data.get('user_in_group')

            if request.data.get('current_user') and user_in_group:
                serializer = UpdateAssignedToIdSerializer(
                        instance=instance,
                        data={
                            'assigned_to_id': request.user.id,
                            }
                        )
            elif user_in_group:
                serializer = UpdateAssignedToIdSerializer(instance=instance, data=request.data)
            
            if serializer:
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    serializer.save()
                    return_serializer = InspectionSerializer(instance=instance,
                            context={'request': request}
                            )
                    headers = self.get_success_headers(return_serializer.data)
                    return Response(
                            return_serializer.data, 
                            status=status.HTTP_201_CREATED,
                            headers=headers
                            )
            else:
                return Response(validation_serializer.data, 
                                status=status.HTTP_201_CREATED
                                )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_renderer_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            returned_data = process_generic_document(request, instance)
            if returned_data:
                return Response(returned_data)
            else:
                return Response()

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_comms_log_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            returned_data = process_generic_document(
                request, 
                instance, 
                document_type='comms_log'
                )
            if returned_data:
                return Response(returned_data)
            else:
                return Response()

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def process_inspection_report_document(self, request, *args, **kwargs):
        print("process_inspection_report_document")
        try:
            #if the action is anything other than list, check auth
            action = request.data.get('action')
            if action != 'list':
                #in-group and assigned OR on inspection team
                if not self.check_authorised_to_update(request, True):
                    return Response(
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
                
            instance = self.get_object()
            returned_data = process_generic_document(
                request, 
                instance, 
                document_type='inspection_report'
                )
            if returned_data:
                print("returned_data")
                print(returned_data)
                filedata = returned_data.get('filedata')
                # Log action if file uploaded
                if filedata and request.data.get('action') == 'save':
                    file_name = filedata[0].get('name')
                    if file_name:
                        instance.log_user_action(
                                InspectionUserAction.ACTION_UPLOAD_INSPECTION_REPORT.format(
                                file_name), request)
                return Response(returned_data)
            else:
                return Response()
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def create(self, request, *args, **kwargs):
        try:

            #to create make sure user is in appropriate group (inspection officer or manager in region)
            if not self.check_authorised_to_create(request):
                return Response(
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            with transaction.atomic():
                # 1. Save Location
                if (
                    request.data.get('location', {}).get('geometry', {}).get('coordinates', {}) or
                    request.data.get('location', {}).get('properties', {}).get('postcode', {}) or
                    request.data.get('location', {}).get('properties', {}).get('details', {})
                ):
                    location_request_data = request.data.get('location')
                    returned_location = save_location(location_request_data)
                    if returned_location:
                        request.data.update({'location_id': returned_location.get('id')})

                serializer = SaveInspectionSerializer(
                        data=request.data, 
                        partial=True
                        )
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    instance = serializer.save()
                    instance.log_user_action(
                            InspectionUserAction.ACTION_CREATE_INSPECTION.format(
                            instance.number), request)
                    # Create comms_log and send mail
                    res = self.workflow_action(request, instance, create_inspection=True)
                    if instance.call_email:
                        print("update parent")
                        self.update_parent(request, instance)
                    return res
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def update_parent(self, request, instance, *args, **kwargs):
        # Log parent actions and update status
        if instance.call_email:
            instance.call_email.log_user_action(
                    CallEmailUserAction.ACTION_ALLOCATE_FOR_INSPECTION.format(
                    instance.call_email.number), request)
            instance.call_email.status = 'open_inspection'
            instance.call_email.save()
            # instance.call_email.close(request)

    @action(detail=True, methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def workflow_action(self, request, instance=None, create_inspection=None, *args, **kwargs):
        print("workflow action")
        print(request.data)
        try:
            with transaction.atomic():
                # email recipient
                #recipient_id = None

                if not create_inspection:
                    if not self.check_authorised_to_update(request):
                        return Response(
                            status=status.HTTP_401_UNAUTHORIZED,
                        )

                if not instance:
                    instance = self.get_object()

                comms_log_id = request.data.get('inspection_comms_log_id')
                if comms_log_id and comms_log_id != 'null':
                    workflow_entry = instance.comms_logs.get(
                            id=comms_log_id)
                else:
                    workflow_entry = self.add_comms_log(request, instance, workflow=True)
                    temporary_document_collection_id = request.data.get('temporary_document_collection_id')
                    if temporary_document_collection_id:
                        temp_doc_collection, created = TemporaryDocumentCollection.objects.get_or_create(
                                id=temporary_document_collection_id)
                        if temp_doc_collection:
                            for doc in temp_doc_collection.documents.all():
                                save_comms_log_document_obj(instance, workflow_entry, doc)
                            temp_doc_collection.delete()

                # Set Inspection status depending on workflow type
                workflow_type = request.data.get('workflow_type')
                if workflow_type == 'send_to_manager':
                    instance.send_to_manager(request)
                elif workflow_type == 'request_amendment':
                    instance.request_amendment(request)
                elif workflow_type == 'endorse':
                    instance.endorse(request)
                elif workflow_type == 'close':
                    instance.close(request)

                #if not workflow_type or workflow_type in ('', ''):
                if create_inspection:
                    instance.region_id = None if not request.data.get('region_id') else request.data.get('region_id')
                    instance.district_id = None if not request.data.get('district_id') else request.data.get('district_id')
                    instance.assigned_to_id = None if not request.data.get('assigned_to_id') else request.data.get('assigned_to_id')
                    instance.inspection_type_id = None if not request.data.get('inspection_type_id') else request.data.get('inspection_type_id')
                    #instance.allocated_group_id = None if not request.data.get('allocated_group_id') else request.data.get('allocated_group_id')
                    instance.call_email_id = None if not request.data.get('call_email_id') else request.data.get('call_email_id')
                    instance.legal_case_id = None if not request.data.get('legal_case_id') else request.data.get('legal_case_id')
                    instance.details = None if not request.data.get('details') else request.data.get('details')
                #elif workflow_type not in ('send_to_manager', 'request_amendment'):
                 #   instance.assigned_to_id = None if not request.data.get('assigned_to_id') else request.data.get('assigned_to_id')
                else:
                    instance.assigned_to_id = None
                    #instance.allocated_group_id = None if not request.data.get('allocated_group_id') else request.data.get('allocated_group_id')
                    #recipient_id = instance.inspection_team_lead_id

                allocated_group = instance.get_compliance_permission_group(instance.region,instance.district,instance.status)
                if not allocated_group and not instance.status in [Inspection.STATUS_CLOSED,
                    Inspection.STATUS_PENDING_CLOSURE,Inspection.STATUS_DISCARDED]:
                    raise serializers.ValidationError("No allocated group for specified region/district")
                instance.allocated_group = allocated_group
                instance.save()
                
                # Needed for create inspection
                if create_inspection:
                    instance = self.modify_inspection_team(request, instance, workflow=True, new=True, user_id=instance.assigned_to_id)

                # send email
                if workflow_type == 'send_to_manager':
                    email_data = prepare_mail(
                            request, 
                            instance, 
                            workflow_entry, 
                            send_mail, 
                            recipient_id=instance.inspection_team_lead_id,
                            email_type='send_to_manager')
                elif workflow_type == 'request_amendment':
                    email_data = prepare_mail(
                            request, 
                            instance, 
                            workflow_entry, 
                            send_mail, 
                            email_type='request_amendment')
                elif workflow_type == 'endorse':
                    email_data = prepare_mail(
                            request, 
                            instance, 
                            workflow_entry, 
                            send_mail, 
                            email_type='endorse')
                else:
                    email_data = prepare_mail(request, instance, workflow_entry, send_mail)

                serializer = InspectionCommsLogEntrySerializer(instance=workflow_entry, data=email_data, partial=True)
                serializer.is_valid(raise_exception=True)
                if serializer.is_valid():
                    serializer.save()
                    return_serializer = InspectionSerializer(instance=instance, 
                            context={'request': request}
                            ) 
                    headers = self.get_success_headers(return_serializer.data)
                    return Response(
                            return_serializer.data, 
                            status=status.HTTP_201_CREATED,
                            headers=headers
                            )
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))
    
    @action(detail=True, methods=['POST'])
    @renderer_classes((JSONRenderer,))
    def create_inspection_process_comms_log_document(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # process docs
            returned_data = process_generic_document(request, instance, document_type='comms_log')
            # delete Inspection if user cancels modal
            action = request.data.get('action')
            if action == 'cancel' and returned_data:
                # returned_data = instance.delete()
                instance.status = 'discarded'
                instance.save()
            # return response
            if returned_data:
                return Response(returned_data)
            else:
                return Response()

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class InspectionTypeViewSet(viewsets.ReadOnlyModelViewSet):
   queryset = InspectionType.objects.none()
   serializer_class = InspectionTypeSerializer

   def get_queryset(self):
       # user = self.request.user
       if is_compliance_internal_user(self.request):
           return InspectionType.objects.all()
       return InspectionType.objects.none()

   @action(detail=True, methods=['GET',])
   @renderer_classes((JSONRenderer,))
   def get_schema(self, request, *args, **kwargs):
       instance = self.get_object()
       try:
           serializer = InspectionTypeSchemaSerializer(instance)
           return Response(
               serializer.data,
               status=status.HTTP_201_CREATED,
               )
       except serializers.ValidationError:
           print(traceback.print_exc())
           raise
       except ValidationError as e:
           print(traceback.print_exc())
           raise serializers.ValidationError(repr(e.error_dict))
       except Exception as e:
           print(traceback.print_exc())
           raise serializers.ValidationError(str(e))

