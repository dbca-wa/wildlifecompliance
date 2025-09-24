import traceback
import base64
import geojson
from six.moves.urllib.parse import urlparse
from wsgiref.util import FileWrapper
from django.db.models import Q, Min
from django.db import transaction
from django.http import HttpResponse
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Value
from django.db.models.functions import Concat
from rest_framework import viewsets, serializers, status, generics, views, mixins
from rest_framework.decorators import action, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser, BasePermission
from rest_framework.pagination import PageNumberPagination
from datetime import datetime, timedelta
from collections import OrderedDict
from django.core.cache import cache
from ledger_api_client.ledger_models import EmailUserRO as EmailUser, Address as OrganisationAddress
from ledger_api_client.country_models import Country
from datetime import datetime, timedelta, date
from wildlifecompliance.helpers import is_customer, is_internal, is_wildlife_compliance_officer
from wildlifecompliance.components.organisations.models import (
    Organisation,
    OrganisationContact,
    OrganisationRequest,
    OrganisationRequestUserAction,
    OrganisationContact,
    OrganisationRequestLogEntry,
    OrganisationAction,
)

from wildlifecompliance.components.organisations.serializers import (
    OrganisationSerializer,
    DTOrganisationSerializer,
    OrganisationAddressSerializer,
    DetailsSerializer,
    OrganisationRequestSerializer,
    OrganisationRequestDTSerializer,
    OrganisationContactSerializer,
    OrganisationContactCheckSerializer,
    OrganisationCheckSerializer,
    OrganisationPinCheckSerializer,
    OrganisationRequestActionSerializer,
    OrganisationActionSerializer,
    OrganisationRequestCommsSerializer,
    OrganisationCommsSerializer,
    OrgUserCheckSerializer,
    OrgUserAcceptSerializer,
    MyOrganisationsSerializer,
    OrganisationCheckExistSerializer,
    ComplianceManagementSaveOrganisationSerializer,
    ComplianceManagementOrganisationSerializer,
    #ComplianceManagementCreateLedgerOrganisationSerializer,
    #ComplianceManagementUpdateLedgerOrganisationSerializer,
    ComplianceManagementSaveOrganisationAddressSerializer,
)
from wildlifecompliance.components.applications.serializers import (
    BaseApplicationSerializer,
)

from wildlifecompliance.components.organisations.emails import (
    send_organisation_address_updated_email_notification,
)


from wildlifecompliance.components.applications.models import (
    Application,
    Assessment,
    ApplicationRequest,
    ActivityPermissionGroup
)
from wildlifecompliance.components.main.process_document import process_generic_document

from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer


class OrganisationFilterBackend(DatatablesFilterBackend):
    """
    Custom filters
    """
    def filter_queryset(self, request, queryset, view):

        #TODO rework - we cannot search on ledger organisation fields

        # Get built-in DRF datatables queryset first to join with search text, then apply additional filters
        super_queryset = super(OrganisationFilterBackend, self).filter_queryset(request, queryset, view).distinct()
        print(super_queryset.count())

        total_count = queryset.count()
        search_text = request.GET.get('search[value]')
        organisation_name = request.GET.get('organisation')
        applicant = request.GET.get('applicant')
        role = request.GET.get('role')
        status = request.GET.get('status')

        if queryset.model is OrganisationRequest:
            # search_text filter, join all custom search columns
            # where ('searchable: false' in the datatable definition)
            if search_text:
                search_text = search_text.lower()
                # join queries for the search_text search
                search_text_org_request_ids = []

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

                search_text_org_request_ids = OrganisationRequest.objects.filter(
                    Q(assigned_officer_id__in=email_user_ids) |
                    Q(requester_id__in=email_user_ids) 
                ).values('id')

                print(search_text_org_request_ids.count())

                # for organisation_request in queryset:
                #     if search_text in organisation_request.address_string.lower():
                #         search_text_org_request_ids.append(organisation_request.id)
                # use pipe to join both custom and built-in DRF datatables querysets (returned by super call above)
                # (otherwise they will filter on top of each other)
                queryset = queryset.filter(id__in=search_text_org_request_ids).distinct() | super_queryset
                print(queryset.count())


            role = role.lower() if role else 'all'
            if role != 'all':
                queryset = queryset.filter(role__iexact=role)
            
            status = status.lower().replace(" ","_") if status else 'all'
            if status != 'all':
                queryset = queryset.filter(status__iexact=status)

        # override queryset ordering, required because the ordering is usually handled
        # in the super call, but is then clobbered by the custom queryset joining above
        # also needed to disable ordering for all fields for which data is not an
        # Organisation model field, as property functions will not work with order_by
        fields = self.get_fields(request)
        ordering = self.get_ordering(request, view, fields)
        if len(ordering):
            queryset = queryset.order_by(*ordering)

        setattr(view, '_datatables_total_count', total_count)
        return queryset


#class OrganisationRenderer(DatatablesRenderer):
#    def render(self, data, accepted_media_type=None, renderer_context=None):
#        if 'view' in renderer_context and hasattr(renderer_context['view'], '_datatables_total_count'):
#            data['recordsTotal'] = renderer_context['view']._datatables_total_count
#        return super(OrganisationRenderer, self).render(data, accepted_media_type, renderer_context)


class OrganisationPaginatedViewSet(viewsets.ReadOnlyModelViewSet):
    #filter_backends = (OrganisationFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    #renderer_classes = (OrganisationRenderer,)
    queryset = Organisation.objects.none()
    serializer_class = DTOrganisationSerializer
    page_size = 10

    def get_queryset(self):
        if is_wildlife_compliance_officer(self.request):
            return Organisation.objects.all() #TODO auth group
        #elif is_customer(self.request):
        #    return Organisation.objects.none()
        return Organisation.objects.none()

    @action(detail=False, methods=['GET', ])
    def datatable_list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = DTOrganisationSerializer(result_page, context={'request': request}, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class OrganisationViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Organisation.objects.none()
    serializer_class = OrganisationSerializer

    def get_queryset(self):
        user = self.request.user
        if is_wildlife_compliance_officer(self.request):
            return Organisation.objects.all() 
        elif user.is_authenticated:
            #org_contacts = OrganisationContact.objects.filter(is_admin=True).filter(email=user.email)
            #user_admin_orgs = [org.organisation.id for org in org_contacts]
            #return Organisation.objects.filter(id__in=user_admin_orgs)
            return user.wildlifecompliance_organisations.all()
        return Organisation.objects.none()

    @action(detail=True, methods=['GET'])
    @renderer_classes((JSONRenderer,))
    def get_intelligence_text(self, request, *args, **kwargs):
        try:
            if is_wildlife_compliance_officer(self.request):
                instance = self.get_object()
                intelligence_text = instance.intelligence_information_text
                return Response({"intelligence_text": intelligence_text})
            else:
                raise serializers.ValidationError("user not authorised")

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
    def save_intelligence_text(self, request, *args, **kwargs):
        try:
            if is_wildlife_compliance_officer(self.request):
                instance = self.get_object()
                intelligence_text = request.data.get('intelligence_text')
                instance.intelligence_information_text = intelligence_text
                instance.save()
                return Response()
            else:
                raise serializers.ValidationError("user not authorised")

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
    def process_intelligence_document(self, request, *args, **kwargs):
        try:
            if is_wildlife_compliance_officer(self.request):
                instance = self.get_object()
                # process docs
                returned_data = process_generic_document(request, instance, 'intelligence_document')
                # delete Sanction Outcome if user cancels modal
                action = request.data.get('action')
                if action == 'cancel' and returned_data:
                    instance.status = 'discarded'
                    instance.save()

                # return response
                if returned_data:
                    return Response(returned_data)
                else:
                    return Response()
            else:
                raise serializers.ValidationError("user not authorised")

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

    @action(detail=True, methods=['GET', ])
    def contacts(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if is_wildlife_compliance_officer(self.request) or instance.can_user_edit(request.user.email):
                serializer = OrganisationContactSerializer(
                instance.contacts.all(), many=True)
                return Response(serializer.data)
            else:
                raise serializers.ValidationError("user not authorised")
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
    def contacts_linked(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if is_wildlife_compliance_officer(self.request) or instance.can_user_edit(request.user.email):
                qs = self.get_queryset()
                serializer = OrganisationContactSerializer(qs, many=True)
                return Response(serializer.data)
            else:
                raise serializers.ValidationError("user not authorised")
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
    def contacts_exclude(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if is_wildlife_compliance_officer(self.request) or instance.can_user_edit(request.user.email):
                qs = instance.contacts.exclude(user_status=OrganisationContact.ORG_CONTACT_STATUS_DRAFT)
                serializer = OrganisationContactSerializer(qs, many=True)
                return Response(serializer.data)
            else:
                raise serializers.ValidationError("user not authorised")
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
    def add_nonuser_contact(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")

            serializer = OrganisationContactCheckSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            admin_flag = False
            role = OrganisationContact.ORG_CONTACT_ROLE_USER
            status = OrganisationContact.ORG_CONTACT_STATUS_DRAFT

            with transaction.atomic():

                OrganisationContact.objects.create(
                    organisation=instance,
                    first_name=request.data.get('first_name'),
                    last_name=request.data.get('last_name'),
                    mobile_number=request.data.get('mobile_number',''),
                    phone_number=request.data.get('phone_number'),
                    fax_number=request.data.get('fax_number',''),
                    email=request.data.get('email'),
                    user_role=role,
                    user_status=status,
                    is_admin=admin_flag
                )

                instance.log_user_action(
                    OrganisationAction.ACTION_CONTACT_ADDED.format(
                        '{} {}({})'.format(
                            request.data.get('first_name'),
                            request.data.get('last_name'),
                            request.data.get('email')
                        )
                    ), 
                    request
                )

            serializer = self.get_serializer(instance)

            return Response(serializer.data)

        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=True, methods=['POST', ])
    def validate_pins(self, request, *args, **kwargs):
        try:
            instance = Organisation.objects.get(id=request.data.get('id'))
            serializer = OrganisationPinCheckSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            with transaction.atomic():
                data = {
                    'valid': instance.validate_pins(
                        serializer.validated_data['pin1'],
                        serializer.validated_data['pin2'],
                        request)}

            if data['valid']:
                # Notify each Admin member of request.
                instance.send_organisation_request_link_notification(request)
            return Response(data)
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
    def accept_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            serializer = OrgUserAcceptSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.accept_user(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def accept_declined_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            serializer = OrgUserAcceptSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.accept_declined_user(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def decline_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            serializer = OrgUserAcceptSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.decline_user(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def unlink_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            request.data.update([('org_id', instance.id)])
            serializer = OrgUserCheckSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.unlink_user(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def make_admin_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            serializer = OrgUserAcceptSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.make_admin_user(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def make_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            request.data.update([('org_id', instance.id)])
            serializer = OrgUserCheckSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.make_user(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def make_consultant(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            request.data.update([('org_id', instance.id)])
            serializer = OrgUserCheckSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.make_consultant(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def suspend_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            request.data.update([('org_id', instance.id)])
            serializer = OrgUserCheckSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.suspend_user(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def reinstate_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            serializer = OrgUserAcceptSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.reinstate_user(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def relink_user(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if not instance.can_user_edit(request.user.email):
                raise serializers.ValidationError("user not authorised")
            serializer = OrgUserAcceptSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user_obj = EmailUser.objects.get(
                email=serializer.validated_data['email']
            )
            instance.relink_user(user_obj, request)
            serializer = self.get_serializer(instance)
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
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if is_wildlife_compliance_officer(request) or instance.can_user_edit(request.user.email):
                qs = instance.action_logs.all()
                serializer = OrganisationActionSerializer(qs, many=True)
                return Response(serializer.data)
            else:
                raise serializers.ValidationError("user not authorised")
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
    def applications(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.org_applications.all()
            serializer = BaseApplicationSerializer(qs, many=True, context={'request': request})
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
            if is_wildlife_compliance_officer(request) or instance.can_user_edit(request.user.email):
                qs = instance.comms_logs.all()
                serializer = OrganisationCommsSerializer(qs, many=True)
                return Response(serializer.data)
            else:
                raise serializers.ValidationError("user not authorised")
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @action(detail=False, methods=['POST', ])
    def existence(self, request, *args, **kwargs):
        try:
            serializer = OrganisationCheckSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = Organisation.existence(serializer.validated_data['abn'])
            # Check request user cannot be relinked to org.
            data.update([('user', request.user.id)])
            data.update([('abn', request.data['abn'])])
            serializer = OrganisationCheckExistSerializer(data=data)
            serializer.is_valid(raise_exception=True)
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
        

class OrganisationRequestsPaginatedViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (OrganisationFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    #renderer_classes = (OrganisationRenderer,)
    queryset = OrganisationRequest.objects.none()
    serializer_class = OrganisationRequestDTSerializer
    page_size = 10

    def get_queryset(self):
        if is_wildlife_compliance_officer(self.request):
            return OrganisationRequest.objects.all()
        #elif is_customer(self.request):
        #    return OrganisationRequest.objects.none()
        return OrganisationRequest.objects.none()

    @action(detail=False, methods=['GET', ])
    def datatable_list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset = self.filter_queryset(queryset)
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = OrganisationRequestDTSerializer(result_page, context={'request': request}, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class OrganisationRequestsViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = OrganisationRequest.objects.none()
    serializer_class = OrganisationRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if is_wildlife_compliance_officer(self.request):
            return OrganisationRequest.objects.all() 
        elif user.is_authenticated:
            return user.organisationrequest_set.all()
        return OrganisationRequest.objects.none()

    @action(detail=False, methods=['GET', ])
    def datatable_list(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset()
            serializer = OrganisationRequestDTSerializer(
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
    def get_pending_requests(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset().filter(requester=request.user, status=OrganisationRequest.ORG_REQUEST_STATUS_WITH_ASSESSOR)
            serializer = OrganisationRequestDTSerializer(qs, many=True, context={'request': request})
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
    def get_amendment_requested_requests(self, request, *args, **kwargs):
        try:
            qs = self.get_queryset().filter(
                requester=request.user, status=OrganisationRequest.ORG_REQUEST_STATUS_AMENDMENT_REQUESTED)
            serializer = OrganisationRequestDTSerializer(qs, many=True, context={'request': request})
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
    def assign_to_me(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(request):
                return Response("user not authorised to assign organisation request")
            instance = self.get_object()
            user = request.user
            if not request.user.has_perm('wildlifecompliance.organisation_access_request'):
                raise serializers.ValidationError(
                    'You do not have permission to process organisation access requests')
            instance.assign_officer(request.user, request)
            serializer = OrganisationRequestSerializer(
                instance, context={'request': request})
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
    def assign_officer(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(request):
                return Response("user not authorised to assign organisation request")

            instance = self.get_object()
            user_id = request.data.get('officer_id', None)
            user = None
            if not user_id:
                raise serializers.ValiationError('An officer id is required')
            try:
                user = EmailUser.objects.get(id=user_id)
            except EmailUser.DoesNotExist:
                raise serializers.ValidationError(
                    'A user with the id passed in does not exist')
            if not request.user.has_perm('wildlifecompliance.organisation_access_request'):
                raise serializers.ValidationError(
                    'You do not have permission to process organisation access requests')

            instance.assign_officer(user, request)
            serializer = OrganisationRequestSerializer(
                instance, context={'request': request})
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
    def unassign_officer(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(request):
                return Response("user not authorised to unassign organisation request")

            instance = self.get_object()
            instance.unassign_officer(request)
            serializer = OrganisationRequestSerializer(
                instance, context={'request': request})
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
    def accept(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(request):
                return Response("user not authorised to accept organisation request")
            
            instance = self.get_object()
            instance.accept(request)
            serializer = OrganisationRequestSerializer(
                instance, context={'request': request})
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
    def amendment_request(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(request):
                return Response("user not authorised to create amendemnt request for organisation request")
            
            instance = self.get_object()
            instance.amendment_request(request)
            serializer = OrganisationRequestSerializer(
                instance, context={'request': request})
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

    @action(detail=True, methods=['PUT', ])
    def reupload_identification_amendment_request(
            self, request, *args, **kwargs):
        try:            
            instance = self.get_object()
            instance.reupload_identification_amendment_request(request)
            serializer = OrganisationRequestSerializer(
                instance, partial=True, context={'request': request})
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
    def decline(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(request):
                return Response("user not authorised to decline organisation request")
            
            instance = self.get_object()
            instance.decline(request)
            serializer = OrganisationRequestSerializer(
                instance, context={'request': request})
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
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = OrganisationRequestActionSerializer(qs, many=True)
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
            serializer = OrganisationRequestCommsSerializer(qs, many=True)
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
    def get_access_selects(self, request, *args, **kwargs):
        '''
        Returns all drop-down lists for OAR dashboard.
        '''
        try:
            all_status = []
            for i in OrganisationRequest.STATUS_CHOICES:
                all_status.append(i[1])

            all_roles = []
            for i in OrganisationRequest.ROLE_CHOICES:
                all_roles.append(i[1])

            return Response({"all_status":list(set(all_status)),"all_roles":list(set(all_roles))})

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.validated_data['requester'] = request.user
            if request.data['role'] == OrganisationRequest.ORG_REQUEST_ROLE_CONSULTANT:
                # Check if consultant can be relinked to org.
                data = Organisation.existence(request.data['abn'])
                data.update([('user', request.user.id)])
                data.update([('abn', request.data['abn'])])
                existing_org = OrganisationCheckExistSerializer(data=data)
                existing_org.is_valid(raise_exception=True)
            with transaction.atomic():
                instance = serializer.save()
                instance.log_user_action(
                    OrganisationRequestUserAction.ACTION_LODGE_REQUEST.format(
                        instance.id), request)
                instance.send_organisation_request_email_notification(request)
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


class OrganisationAccessGroupMembers(views.APIView):

    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        members = []
        if is_wildlife_compliance_officer(request):
            groups = ActivityPermissionGroup.objects.filter(
                permissions__codename__in=[
                    'organisation_access_request',
                    'system_administrator'
                ]
            )
            for group in groups:
                for member in group.members:
                    members.append({'name': member.get_full_name(), 'id': member.id})
        return Response(members)


class OrganisationContactViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    serializer_class = OrganisationContactSerializer
    queryset = OrganisationContact.objects.none()

    def get_queryset(self):
        user = self.request.user
        if is_wildlife_compliance_officer(self.request):
            return OrganisationContact.objects.all()
        elif user.is_authenticated:

            org_contacts = OrganisationContact.objects.filter(is_admin=True).filter(email=user.email)
            user_admin_orgs = [org.organisation.id for org in org_contacts]
            return OrganisationContact.objects.filter(Q(organisation_id__in=user_admin_orgs) | Q(email=user.email))

        return OrganisationContact.objects.none()
    
    @action(detail=True, methods=['DELETE', ])
    def delete(self, request, *args, **kwargs):
        # only allowed to remove organisation contacts if their status is in draft
        try:
            instance = self.get_object()
            with transaction.atomic():
                if instance.user_status == 'draft':
                    instance.delete()
                else:
                    return Response("Cannot delete this organisation contact.")

            serializer = self.get_serializer(instance)
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


class MyOrganisationsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Organisation.objects.none()
    serializer_class = MyOrganisationsSerializer

    def get_queryset(self):
        user = self.request.user
        if is_wildlife_compliance_officer(self.request):
            return Organisation.objects.all()
        elif user.is_authenticated:
            return user.wildlifecompliance_organisations.all()
        return Organisation.objects.none()

class OrganisationComplianceManagementViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = Organisation.objects.none()
    serializer_class = ComplianceManagementOrganisationSerializer
    
    def get_queryset(self):
        user = self.request.user
        if is_wildlife_compliance_officer(self.request):
            return Organisation.objects.all()
        elif user.is_authenticated:
            return user.wildlifecompliance_organisations.all()
        return Organisation.objects.none()

    #TODO: consider removing - it does appear to be in use
    def create(self, request, *args, **kwargs):
        print("create org")
        print(request.data)

        #auth, in case it is used
        if not is_wildlife_compliance_officer(request):
            return Response("user not authorised to create",
            status=status.HTTP_401_UNAUTHORIZED)

        try:
            with transaction.atomic():
                abn = request.data.get('abn')
                address = request.data.get('address')
                ledger_org = None
                wc_org = None

                if not abn:
                    return Response({'message': 'ABN must be specified'}, status=status.HTTP_400_BAD_REQUEST)

                organisation_response = get_search_organisation(None, abn)
                response_status = organisation_response.get("status", None)

                ledger_org_list = []
                if response_status == status.HTTP_200_OK:
                    ledger_org_list = organisation_response.get("data", {})[0]

                if ledger_org_list:
                    ledger_org = ledger_org_list[0]
                if ledger_org:
                    wc_org_list = Organisation.objects.filter(organisation_id=ledger_org["organisation_id"])
                    if wc_org_list:
                        wc_org = wc_org_list[0]
                        return Response({'message': 'WC org already exists'}, status=status.HTTP_400_BAD_REQUEST)
                if address:
                    if ledger_org and ledger_org_address:
                        print("existing address")
                        ledger_org_address = ledger_org.adresses.first()
                        address_serializer = ComplianceManagementSaveOrganisationAddressSerializer(
                                instance=ledger_org_address, 
                                data=address)
                    else:
                        print("no existing address")
                        address_serializer = ComplianceManagementSaveOrganisationAddressSerializer(
                                data=address)
                    address_serializer.is_valid(raise_exception=True)
                    if address_serializer.is_valid:
                        saved_address = address_serializer.save()
                        print("address saved") 
                # WC only cares about the postal address
                #saved_address = update_or_create_postal_address(address, ledger_org)
                saved_address = self.update_postal_address(address, ledger_org) #NOTE: this would have been broken for some time
                ledger_org_data = {'name': request.data.get('name'),
                        'abn': request.data.get('abn'),
                        'postal_address_id': saved_address.id
                        }
                
                #TODO fix or replace for segregation
                #if ledger_org:
                #    # update existing ledger_org
                #    ledger_serializer = ComplianceManagementUpdateLedgerOrganisationSerializer(instance=ledger_org.id, data=ledger_org_data)
                #else:
                #    # create ledger_org if it doesn't exist
                #    ledger_serializer = ComplianceManagementCreateLedgerOrganisationSerializer(data=ledger_org_data)
                #ledger_serializer.is_valid(raise_exception=True)
                #if ledger_serializer.is_valid:
                #    ledger_org = ledger_serializer.save()
                #    org_serializer = ComplianceManagementSaveOrganisationSerializer(data={'organisation_id': ledger_org.id})
                #    org_serializer.is_valid(raise_exception=True)
                #    if org_serializer.is_valid:
                #        org_serializer.save()
                #        # return serialized data for all objects
                #        content = {'ledger_org': ledger_serializer.data, 
                #                    'wc_org': org_serializer.data,
                #                    'ledger_address': address_serializer.data
                #                    }
                #        return Response(content, status=status.HTTP_201_CREATED)

            return Response({'message': 'No org created'}, status=status.HTTP_400_BAD_REQUEST)
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
    def update_postal_address(self, request, *args, **kwargs):
        print("create org")
        print(request.data)
        try:
            instance = self.get_object()
            postal_address = instance.organisation.postal_address
            address = request.data.get('address')
            if address:
                address_serializer = ComplianceManagementSaveOrganisationAddressSerializer(
                        instance=postal_address, 
                        data=address)
                address_serializer.is_valid(raise_exception=True)
                if address_serializer.is_valid:
                    saved_address = address_serializer.save()
                    print("address saved") 
                    return Response(address_serializer.data, status=status.HTTP_201_CREATED)

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    #def update_or_create_postal_address(address, ledger_org=None):
    #    if ledger_org and ledger_org.postal_address:
    #        print("existing address")
    #        #ledger_org_address = ledger_org.adresses.first()
    #        address_serializer = ComplianceManagementSaveOrganisationAddressSerializer(
    #                instance=ledger_org.postal_address, 
    #                data=address)
    #    else:
    #        print("no existing address")
    #        address_serializer = ComplianceManagementSaveOrganisationAddressSerializer(
    #                data=address)

    #    address_serializer.is_valid(raise_exception=True)
    #    if address_serializer.is_valid:
    #        saved_address = address_serializer.save()
    #        print("address saved")
    #    return saved_address


class GetOrganisationId(views.APIView):
    renderer_classes = [JSONRenderer,]

    def get(self, request, format=None):

        org_id = request.GET.get('org_id', '')
        user = self.request.user
        if is_wildlife_compliance_officer(request):
            organisation_qs = Organisation.objects.filter(organisation_id=org_id)
        elif user.is_authenticated:
            organisation_qs = user.wildlifecompliance_organisations.filter(organisation_id=org_id)

        if organisation_qs.exists():
            return Response({"id":organisation_qs.last().id})
        else:
            serializers.ValidationError("not authorised to access organisation")