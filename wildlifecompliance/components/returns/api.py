import traceback
import logging
from datetime import datetime, timedelta
from django.urls import reverse
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ValidationError
from rest_framework import viewsets, serializers, status, views, mixins
from rest_framework.decorators import (
    detail_route,
    list_route,
    renderer_classes,
)
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from rest_framework_datatables.pagination import DatatablesPageNumberPagination
from rest_framework_datatables.filters import DatatablesFilterBackend
from rest_framework_datatables.renderers import DatatablesRenderer

from ledger.checkout.utils import calculate_excl_gst

from wildlifecompliance.helpers import is_customer, is_internal, is_wildlife_compliance_officer
from wildlifecompliance.components.returns.utils import (
    SpreadSheet,
    checkout,
    set_session_return,
    delete_session_return,
)
from wildlifecompliance.components.licences.models import (
    WildlifeLicence
)
from wildlifecompliance.components.returns.models import (
    Return,
    ReturnType,
)
from wildlifecompliance.components.returns.serializers import (
    ReturnSerializer,
    ReturnActionSerializer,
    ReturnLogEntrySerializer,
    ReturnTypeSerializer,
    ReturnRequestSerializer,
    DTExternalReturnSerializer,
    DTInternalReturnSerializer,
)
from wildlifecompliance.components.applications.models import (
    Application,
    ReturnRequest,
)

from wildlifecompliance.components.returns.email import (
    send_return_amendment_email_notification,
)
from wildlifecompliance.components.returns.services import (
    ReturnService,
    ReturnData,
)

from wildlifecompliance.components.main.utils import (
    get_first_name,
    get_last_name,
)

logger = logging.getLogger(__name__)
# logger = logging


class ReturnFilterBackend(DatatablesFilterBackend):
    """
    Custom filters
    """
    def filter_queryset(self, request, queryset, view):

        # Get built-in DRF datatables queryset first to join with search text,
        # then apply additional filters.
        super_queryset = super(ReturnFilterBackend, self).filter_queryset(
            request, queryset, view).distinct().order_by('-id')

        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        status = request.GET.get('status')
        queryset = super_queryset

        if queryset.model is Return:

            # apply user selected filters
            status = status.lower() if status else 'all'
            if status != 'all':
                status_ids = []
                for returns in queryset:
                    if status in returns.processing_status.lower():
                        status_ids.append(returns.id)
                queryset = queryset.filter(id__in=status_ids).distinct()
            if date_from:
                date_from = datetime.strptime(
                    date_from, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(due_date__gte=date_from)
            if date_to:
                date_to = datetime.strptime(
                    date_to, '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(due_date__lte=date_to)

        return queryset


#class ReturnRenderer(DatatablesRenderer):
#    def render(self, data, accepted_media_type=None, renderer_context=None):
#        if 'view' in renderer_context and \
#                hasattr(renderer_context['view'], '_datatables_total_count'):
#            data['recordsTotal'] = \
#                renderer_context['view']._datatables_total_count
#        return super(ReturnRenderer, self).render(
#            data, accepted_media_type, renderer_context)


class ReturnPaginatedViewSet(viewsets.ReadOnlyModelViewSet):
    filter_backends = (ReturnFilterBackend,)
    pagination_class = DatatablesPageNumberPagination
    #renderer_classes = (ReturnRenderer,)
    queryset = Return.objects.none()
    serializer_class = DTExternalReturnSerializer
    page_size = 10

    def get_queryset(self):
        user = self.request.user

        if is_wildlife_compliance_officer(self.request):
            return Return.objects.all()

        elif user.is_authenticated():
            user_orgs = [
                org.id for org in user.wildlifecompliance_organisations.all()]
            user_licences = [wildlifelicence.id for wildlifelicence in WildlifeLicence.objects.filter(
                Q(current_application__org_applicant_id__in=user_orgs) |
                Q(current_application__proxy_applicant=user) |
                Q(current_application__submitter=user))]
            
            external_qs = Return.objects.filter(
                Q(licence_id__in=user_licences)
            ).exclude(
                processing_status=Return.RETURN_PROCESSING_STATUS_DISCARDED
            ).distinct()

            return external_qs

        return Return.objects.none()

    @list_route(methods=['GET', ])
    def user_datatable_list(self, request, *args, **kwargs):
        self.serializer_class = ReturnSerializer
        queryset = self.get_queryset()
        # Filter by org
        org_id = request.GET.get('org_id', None)
        if org_id:
            queryset = queryset.filter(licence__current_application__org_applicant_id=org_id)
        # Filter by proxy_applicant
        proxy_applicant_id = request.GET.get('proxy_applicant_id', None)
        if proxy_applicant_id:
            queryset = queryset.filter(proxy_applicant_id=proxy_applicant_id)
        # Filter by submitter
        submitter_id = request.GET.get('submitter_id', None)
        if submitter_id:
            queryset = queryset.filter(submitter_id=submitter_id)
        # Filter by user (submitter or proxy_applicant)
        user_id = request.GET.get('user_id', None)
        if user_id:
            applications = Application.objects.filter(
                Q(proxy_applicant=user_id) |
                Q(submitter=user_id)
            )
            queryset = queryset.filter(application__in=applications)
        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = DTInternalReturnSerializer(
            result_page, context={'request': request}, many=True)
        return self.paginator.get_paginated_response(serializer.data)

    @list_route(methods=['GET', ])
    def external_datatable_list(self, request, *args, **kwargs):
        self.serializer_class = ReturnSerializer
        queryset = self.get_queryset()
        # Filter by org
        org_id = request.GET.get('org_id', None)
        if org_id:
            queryset = queryset.filter(org_applicant_id=org_id)
        # Filter by proxy_applicant
        proxy_applicant_id = request.GET.get('proxy_applicant_id', None)
        if proxy_applicant_id:
            queryset = queryset.filter(proxy_applicant_id=proxy_applicant_id)
        # Filter by submitter
        submitter_id = request.GET.get('submitter_id', None)
        if submitter_id:
            queryset = queryset.filter(submitter_id=submitter_id)
        # Filter by user (submitter or proxy_applicant)
        user_id = request.GET.get('user_id', None)
        if user_id:
            queryset = Application.objects.filter(
                Q(proxy_applicant=user_id) |
                Q(submitter=user_id)
            )
        queryset = self.filter_queryset(queryset)
        self.paginator.page_size = queryset.count()
        result_page = self.paginator.paginate_queryset(queryset, request)
        serializer = DTExternalReturnSerializer(
            result_page, context={'request': request}, many=True)
        return self.paginator.get_paginated_response(serializer.data)


class ReturnViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    serializer_class = ReturnSerializer
    queryset = Return.objects.none()

    def get_queryset(self):
        user = self.request.user
        if is_wildlife_compliance_officer(self.request):
            return Return.objects.all()
        elif user.is_authenticated():
            user_orgs = [
                org.id for org in user.wildlifecompliance_organisations.all()]
            user_licences = [wildlifelicence.id for wildlifelicence in WildlifeLicence.objects.filter(
                Q(current_application__org_applicant_id__in=user_orgs) |
                Q(current_application__proxy_applicant=user) |
                Q(current_application__submitter=user))]
            return Return.objects.filter(Q(licence_id__in=user_licences))
        return Return.objects.none()
    
    def get_serializer_class(self):
        try:
            return_obj = self.get_object()
            return ReturnSerializer
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e,'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                if hasattr(e,'message'):
                    raise serializers.ValidationError(e.message)
        except AssertionError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        # Filter by org
        org_id = request.GET.get('org_id', None)
        if org_id:
            queryset = queryset.filter(application__org_applicant_id=org_id)
        # Filter by proxy_applicant
        proxy_applicant_id = request.GET.get('proxy_applicant_id', None)
        if proxy_applicant_id:
            queryset = queryset.filter(
                application__proxy_applicant_id=proxy_applicant_id)
        # Filter by submitter
        submitter_id = request.GET.get('submitter_id', None)
        if submitter_id:
            queryset = queryset.filter(application__submitter_id=submitter_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @list_route(methods=['GET', ])
    def user_list(self, request, *args, **kwargs):
        qs = self.get_queryset().exclude(
            processing_status=Return.RETURN_PROCESSING_STATUS_FUTURE
        )

        serializer = ReturnSerializer(qs, many=True)
        return Response(serializer.data)

    @detail_route(methods=['POST', ])
    def accept(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(self.request):
                return Response("user not authorised to accept return")

            logger.debug('ReturnViewSet.accept() - start')
            instance = self.get_object()
            # instance.accept(request)
            ReturnService.accept_return_request(request, instance)
            # serializer = self.get_serializer(instance)
            logger.debug('ReturnViewSet.accept() - end')

            return Response(
                {'return_id': instance.id},
                status=status.HTTP_200_OK
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

    @detail_route(methods=['POST', ])
    def upload_details(self, request, *args, **kwargs):
        try:
            logger.debug('ReturnViewSet.upload_details() - start')
            instance = self.get_object()
            if not instance.has_data:
                return Response(
                    {'error': 'Upload not applicable for Return Type.'},
                    status=status.HTTP_406_NOT_ACCEPTABLE
                )
            spreadsheet = SpreadSheet(
                instance, request.FILES['spreadsheet']).factory()

            if not spreadsheet.is_valid():
                return Response(
                    {'error': 'Enter data in correct format.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            data = ReturnData(instance)
            table = data.build_table(spreadsheet.rows_list)
            logger.debug('ReturnViewSet.upload_details() - end')

            return Response(table)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def species_data_details(self, request, *args, **kwargs):
        species_id = request.GET.get('species_id', None)
        instance = self.get_object()
        data = ReturnService.set_species_for(instance, species_id)

        return Response(data.table)

    @list_route(methods=['GET', ])
    def sheet_details(self, request, *args, **kwargs):
        logger.debug('ReturnViewSet.sheet_details() - start')
        return_id = self.request.query_params.get('return_id')
        species_id = self.request.query_params.get('species_id')
        instance = Return.objects.get(id=return_id)
        sheet = ReturnService.set_species_for(instance, species_id)
        logger.debug('ReturnViewSet.sheet_details() - end')

        return Response(sheet.table)

    @detail_route(methods=['POST', ])
    def sheet_check_transfer(self, request, *args, **kwargs):
        try:
            instance = self.get_object()

            # if not instance.sheet.is_valid_transfer(request):
            #     raise ValidationError({'err': 'Transfer not valid.'})

            # if valid store updated table??
            # ReturnService.store_request_details_for(instance, request)

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

    @detail_route(methods=['POST', ])
    def sheet_pay_transfer(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            product_lines = []

            return_submission = u'Return submitted by {0} {1} confirmation {2}\
                '.format(get_first_name(instance.submitter),
                         get_last_name(instance.submitter),
                         instance.lodgement_number)
            # place return and its table in the session for storing.
            set_session_return(request.session, instance)
            qty = request.data['qty']
            fees = ReturnService.calculate_fees(instance)['fees']['return']
            price = int(qty) * fees
            licence = request.data['licence']
            oracle_code = instance.return_type.oracle_account_code

            product_lines.append({
                'ledger_description': 'Transfer fee to licence {0}'.format(
                    licence),
                'quantity': 1,
                'price_incl_tax': str(price),
                'price_excl_tax': str(calculate_excl_gst(price)),
                'oracle_code': oracle_code
            })

            checkout_result = checkout(
                request, instance,
                lines=product_lines,
                invoice_text=return_submission,
                add_checkout_params={
                    'return_url': request.build_absolute_uri(
                        reverse('external-sheet-success-invoice'))
                },
            )

            return checkout_result
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def submit_and_checkout(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            product_lines = []

            return_submission = u'Return submitted by {0} {1} confirmation {2}\
                '.format(get_first_name(instance.submitter),
                         get_last_name(instance.submitter),
                         instance.lodgement_number)
            set_session_return(request.session, instance)
            product_lines = ReturnService.get_product_lines(instance)
            checkout_result = checkout(request,
                                       instance, lines=product_lines,
                                       invoice_text=return_submission)
            return checkout_result
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

    @detail_route(methods=['POST', ])
    def save(self, request, *args, **kwargs):
        try:
            logger.debug('ReturnViewSet.save() - start')
            instance = self.get_object()

            with transaction.atomic():
                print("saving return")
                ReturnService.store_request_details_for(instance, request)
                instance.save()
                serializer = self.get_serializer(instance)
            logger.debug('ReturnViewSet.save() - end')

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

    @detail_route(methods=['POST', ])
    def save_and_submit(self, request, *args, **kwargs):
        try:
            logger.debug('ReturnViewSet.save_and_submit() - start')
            instance = self.get_object()

            with transaction.atomic():

                ReturnService.store_request_details_for(instance, request)
                instance.set_submitted(request)
                instance.submitter = request.user
                instance.save()

            logger.debug('ReturnViewSet.save_and_submit() - end')

            return Response(
                {'return_id': instance.id},
                status=status.HTTP_200_OK
            )

        except serializers.ValidationError:
            delete_session_return(request.session)
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            delete_session_return(request.session)
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    def submit(self, request, *args, **kwargs):
        try:
            logger.debug('ReturnViewSet.submit() - start')
            instance = self.get_object()

            with transaction.atomic():
                instance.set_submitted(request)
                instance.submitter = request.user
                instance.save()
                serializer = self.get_serializer(instance)
            logger.debug('ReturnViewSet.submit() - end')

            return Response(serializer.data)

        except serializers.ValidationError:
            delete_session_return(request.session)
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            delete_session_return(request.session)
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    def discard(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(self.request):
                return Response("user not authorised to discard return")
            instance = self.get_object()
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

    @detail_route(methods=['POST', ])
    def estimate_price(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            # return_id = request.data.get('return_id')

            return Response({'fees': ReturnService.calculate_fees(instance)})

        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(repr(e.error_dict))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))

    @detail_route(methods=['POST', ])
    def assign_to_me(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(self.request):
                return Response("user not authorised to assign return")
            instance = self.get_object()
            user = request.user

            if user not in instance.activity_curators:
                raise serializers.ValidationError(
                    'You are not in any relevant officer groups.')

            ReturnService.assign_officer_request(request, instance, user)
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

    @detail_route(methods=['POST', ])
    def assign_officer(self, request, *args, **kwargs):
        from ledger.accounts.models import EmailUser
        try:
            if not is_wildlife_compliance_officer(self.request):
                return Response("user not authorised to assign return")
            instance = self.get_object()
            user_id = request.data.get('officer_id', None)
            user = None

            if not user_id:
                raise serializers.ValidationError('An officer id is required')

            try:
                user = EmailUser.objects.get(id=user_id)

            except EmailUser.DoesNotExist:
                raise serializers.ValidationError(
                    'A user with the id passed in does not exist')

            if not request.user.has_perm(
              'wildlifecompliance.return_curator'):
                raise serializers.ValidationError(
                    'You are not authorised to assign officers')

            if user not in instance.activity_curators:
                raise serializers.ValidationError(
                    'User is not in any relevant officer groups')

            ReturnService.assign_officer_request(request, instance, user)
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

    @detail_route(methods=['POST', ])
    def unassign_officer(self, request, *args, **kwargs):
        try:
            if not is_wildlife_compliance_officer(self.request):
                return Response("user not authorised to assign return")
            instance = self.get_object()

            ReturnService.unassign_officer_request(request, instance)
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

    @detail_route(methods=['post'])
    @renderer_classes((JSONRenderer,))
    def officer_comments(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            ReturnService.record_deficiency_request(request, instance)
            serializer = self.get_serializer(instance)

            return Response(serializer.data)

        except Exception as e:
            print(traceback.print_exc())

        raise serializers.ValidationError(str(e))

    @detail_route(methods=['GET', ])
    def comms_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.comms_logs.all()
            serializer = ReturnLogEntrySerializer(qs, many=True)
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

    @detail_route(methods=['POST', ])
    @renderer_classes((JSONRenderer,))
    def add_comms_log(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                instance = self.get_object()
                request_data = request.data.copy()
                request_data['compliance'] = u'{}'.format(instance.id)
                request_data['staff'] = u'{}'.format(request.user.id)
                request_data['return_obj'] = instance.id
                request_data['log_type'] = request.data['type']
                serializer = ReturnLogEntrySerializer(data=request_data)
                serializer.is_valid(raise_exception=True)
                comms = serializer.save()
                # Save the files
                for f in request.FILES:
                    document = comms.documents.create()
                    document.name = str(request.FILES[f])
                    document._file = request.FILES[f]
                    document.save()
                # End Save Documents

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

    @detail_route(methods=['GET', ])
    def action_log(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            qs = instance.action_logs.all()
            serializer = ReturnActionSerializer(qs, many=True)
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


class ReturnTypeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ReturnTypeSerializer
    queryset = ReturnType.objects.none()

    def get_queryset(self):
        if is_wildlife_compliance_officer(self.request):
            return ReturnType.objects.all()
        return ReturnType.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ReturnAmendmentRequestViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    queryset = ReturnRequest.objects.none()
    serializer_class = ReturnRequestSerializer

    def get_queryset(self):
        user = self.request.user
        if is_wildlife_compliance_officer(self.request):
            return ReturnRequest.objects.all()
        elif user.is_authenticated():
            user_orgs = [
                org.id for org in user.wildlifecompliance_organisations.all()]
            user_applications = [application.id for application in Application.objects.filter(
                Q(org_applicant_id__in=user_orgs) | Q(proxy_applicant=user) | Q(submitter=user))]
            return ReturnRequest.objects.filter(
                Q(application_id__in=user_applications))
        return ReturnRequest.objects.none()

    def create(self, request, *args, **kwargs):
        # DRAFT = Return.RETURN_PROCESSING_STATUS_DRAFT
        DUE = Return.RETURN_PROCESSING_STATUS_DUE

        if not is_wildlife_compliance_officer(self.request):
            return Response("user not authorised to create",
            status=status.HTTP_401_UNAUTHORIZED)

        try:

            with transaction.atomic():
                amend_data = self.request.data
                reason = amend_data.pop('reason')
                a_return = amend_data.pop('a_return')
                text = amend_data.pop('text')

                returns = Return.objects.get(id=a_return['id'])
                returns.processing_status = DUE
                returns.save()
                application = a_return['application']
                licence = a_return['licence']
                assigned_to = a_return['assigned_to']
                data = {
                        'application': application,
                        'reason': reason,
                        'text': text,
                        'officer': assigned_to
                }

                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()

            # send email
            send_return_amendment_email_notification(
                request, data, returns, licence)

            serializer = ReturnSerializer(
                returns, context={'request': request}
            )
            # serializer = self.get_serializer(instance)
            # returning amendment.
            return Response(serializer.data)
        except serializers.ValidationError:
            print(traceback.print_exc())
            raise
        except ValidationError as e:
            if hasattr(e, 'error_dict'):
                raise serializers.ValidationError(repr(e.error_dict))
            else:
                logger.error(
                    'ReturnAmendmentRequestViewSet.create(): {0}'.format(e)
                )
                # raise serializers.ValidationError(repr(e[0].encode('utf-8')))
                raise serializers.ValidationError(repr(e[0]))
        except Exception as e:
            print(traceback.print_exc())
            raise serializers.ValidationError(str(e))


class ReturnAmendmentRequestReasonChoicesView(views.APIView):

    renderer_classes = [JSONRenderer, ]

    def get(self, request, format=None):
        choices_list = []
        choices = ReturnRequest.REASON_CHOICES
        if choices:
            for c in choices:
                choices_list.append({'key': c[0], 'value': c[1]})

        return Response(choices_list)
