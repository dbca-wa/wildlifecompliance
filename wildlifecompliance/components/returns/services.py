import abc
import ast
import logging
import datetime

from datetime import date, timedelta

from concurrency.exceptions import RecordModifiedError

from django.core.exceptions import ValidationError, FieldError
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils import timezone

from ledger.checkout.utils import calculate_excl_gst

from wildlifecompliance.exceptions import ReturnServiceException
from wildlifecompliance.components.main.utils import checkout, singleton
from wildlifecompliance.components.main.utils import flush_checkout_session

from wildlifecompliance.components.returns.payments import ReturnFeePolicy
from wildlifecompliance.components.returns.utils_schema import Schema
from wildlifecompliance.components.returns.utils import get_session_return
from wildlifecompliance.components.returns.utils import bind_return_to_invoice
from wildlifecompliance.components.returns.utils import ReturnSpeciesUtility

from wildlifecompliance.components.returns.email import (
    send_sheet_transfer_email_notification,
    send_return_invoice_notification,
    send_return_accept_email_notification,
)
from wildlifecompliance.components.returns.models import (
    Return,
    ReturnType,
    ReturnTable,
    ReturnInvoice,
    ReturnRow,
    ReturnUserAction,
    ReturnActivity,
)

logger = logging.getLogger(__name__)
# logger = logging

'''
Associations:                                        +----------------------+
                                  +----------------  |    WildlifeLicence   |
                                  |                  +----------------------+
                                  V
+----------------+          +------------+           +----------------------+
|   ReturnData   | <--+---  |   Return   | <-------  | ApplicationCondition |
+----------------+    |     +------------+           +----------------------+
+----------------+    |           ^                              |
| ReturnQuestion | <--+           |                              V
+----------------+    |     +------------+           +----------------------+
+----------------+    |     | ReturnType |           |      Application     |
|  ReturnSheet   | <--+     +------------+           +----------------------+
+----------------+
'''


class ReturnService(object):
    '''
    A Facade for the Return (compliance) subsystem responsible for requests.
    '''

    __metaclass__ = abc.ABCMeta

    @staticmethod
    def discard_return_request(request, condition):
        '''
        Discard Return for a Licence Condition.

        :param: ApplicationCondition for the generated Return.
        '''
        logger.debug('ReturnService.discard_return() - start')
        logger_title = '{0} AppID {1} CondID {2}'.format(
            'ReturnService.discard_return()',
            condition.application.id, condition.id
        )
        successful = False
        try:
            command = DiscardRequestCommand(request, condition)
            command.execute()
            successful = True

        except ReturnServiceException as rse:
            log = '{0} {1}'.format(logger_title, rse)
            logger.exception(log)

        except Exception as e:
            log = '{0} {1}'.format(logger_title, e)
            logger.exception(log)
            raise

        logger.debug('ApplicationService.submit_application_request() - end')
        return successful

    @staticmethod
    def generate_return_request(request, licence, selected_activity) -> bool:
        '''
        Services a request for generating Returns for Conditions on the
        Selected Activity for the Wildlife Licence.

        :param: request is an incoming client request.
        :param: licence is a WildlifeLicence for the Return.
        :param: selected_activity is the ApplicationSelectedActivity.
        '''
        logger.debug('ReturnService.generate_return_request() - start')
        logger_title = '{0} AppID {1}'.format(
            'ReturnService.generate_return_request()',
            selected_activity.application_id,
        )
        successful = False
        try:
            generator = ReturnGenerator()
            generator.create_return(request, licence, selected_activity)
            successful = True

        except ReturnServiceException as rse:
            log = '{0} {1}'.format(logger_title, rse)
            logger.exception(log)

        except Exception as e:
            log = '{0} {1}'.format(logger_title, e)
            logger.exception(log)
            raise

        logger.debug('ReturnService.generate_return_request() - end')
        return successful

    @staticmethod
    def etl_return_sheet(real_time=False, return_ids=None) -> bool:
        '''
        A service call to cleanse Return running sheets.

        :param: return_ids is a List of identifiers.
        '''
        logger.debug('ReturnService.etl_return_sheet() - start')
        logger_title = '{0}'.format(
            'ReturnService.etl_return_sheet()',
        )
        successful = False
        try:
            etl = ReturnETL(CleanseReturnSheet(real_time, return_ids))
            etl.process()
            successful = True

        except ReturnServiceException as rse:
            log = '{0} {1}'.format(logger_title, rse)
            logger.exception(log)

        except Exception as e:
            log = '{0} {1}'.format(logger_title, e)
            logger.exception(log)
            raise

        logger.debug('ReturnService.etl_return_sheet() - end')
        return successful

    @staticmethod
    def record_deficiency_request(request, a_return):
        '''
        '''
        if a_return.has_data:
            data = ReturnData(a_return)
            data.store(request)

        if a_return.has_question:
            question = ReturnQuestion(a_return)
            question.store(request)

        return []

    @staticmethod
    def unassign_officer_request(request, a_return):
        '''
        Remove an officer from a reqested return.

        :param request details from view.
        :param a return for assignment.
        '''
        with transaction.atomic():
            try:
                if a_return.assigned_to:
                    a_return.assigned_to = None
                    a_return.save()
                    # Create a log entry.
                    a_return.log_user_action(
                        ReturnUserAction.ACTION_UNASSIGN.format(
                            a_return.id), request)

            except BaseException as e:
                logger.error('ERR: unassign_officer_request : {0}'.format(e))
                raise

    @staticmethod
    def assign_officer_request(request, a_return, an_officer):
        '''
        Assign an officer to requested return.

        :param request details from view.
        :param a return for assignment.
        :param an officer is EmailUser details.
        '''
        with transaction.atomic():
            try:

                if an_officer != a_return.assigned_to:
                    a_return.assigned_to = an_officer
                    a_return.save()

                    # Create a log entry.
                    a_return.log_user_action(
                        ReturnUserAction.ACTION_ASSIGN_TO.format(
                            a_return.id, '{}({})'.format(
                                an_officer.get_full_name(),
                                an_officer.email)
                        ), request)

            except BaseException as e:
                logger.error('ERR: assign_officer_request : {0}'.format(e))
                raise

    @staticmethod
    def accept_return_request(request, a_return):
        '''
        Process an accepted requested return.
        '''
        workflow_status = [
            # Expected status for requested return.
            Return.RETURN_PROCESSING_STATUS_WITH_CURATOR
        ]
        try:
            if a_return.processing_status not in workflow_status:
                raise Exception('Cannot accept a return not with curator.')

            # Set status.
            status = Return.RETURN_PROCESSING_STATUS_ACCEPTED
            a_return.set_processing_status(status)
            # Send notification.
            send_return_accept_email_notification(a_return, request)
            # Log action.
            a_return.log_user_action(
                ReturnUserAction.ACTION_ACCEPT_REQUEST.format(a_return),
                request
            )

        except BaseException as e:
            logger.error('accept_return_request(): {0}'.format(e))
            raise

    @staticmethod
    def submit_session_return_request(request):
        '''
        Process a requested return submission using session attributes from the
        request.

        NOTE: Session is not deleted on successful submission.
        '''
        is_submitted = False
        try:
            the_return = get_session_return(request.session)
            the_return.set_submitted(request)
            is_submitted = True

            logger.info('Submit Successful Return: {0}'.format(
                the_return.id))

        except BaseException as e:
            logger.error('submit_session_return_request(): {0}'.format(e))
            raise

        return is_submitted

    @staticmethod
    def invoice_session_return_request(request):
        '''
        Process a return payment invoice using session attributes from the
        request.

        NOTE: Session is not deleted on successful invoicing.
        '''
        is_invoiced = False
        try:
            the_return = get_session_return(request.session)
            invoice_ref = request.GET.get('invoice')
            bind_return_to_invoice(request, the_return, invoice_ref)
            send_return_invoice_notification(the_return, invoice_ref, request)
            is_invoiced = True

            logger.info('Paid Invoice: {0} Return: {1} Amt: {2}'.format(
                invoice_ref, the_return.id, the_return.return_fee))

        except BaseException as e:
            logger.error('invoice_session_return_request(): {0}'.format(e))
            raise

        return is_invoiced

    @staticmethod
    def calculate_fees(a_return, data_source=None):
        '''
        Calculates fees for a Return.
        '''
        # update any fees.
        fee_policy = ReturnFeePolicy.get_fee_policy_for(a_return)
        fee_policy.set_return_fee()  # force a re-calculation.

        return fee_policy.get_dynamic_attributes()

    @staticmethod
    def get_product_lines(a_return):
        '''
        Get product lines for fees associated with a return to be charged
        through checkout.
        '''
        return ReturnFeePolicy.get_fee_product_lines_for(a_return)

    @staticmethod
    def verify_due_return_id(return_id):
        '''
        Vertification of return due date for a single return.
        '''
        ReturnService.verify_due_returns(return_id, False)

    @staticmethod
    def verify_due_returns(id=0, for_all=True):
        '''
        Vertification of return due date seven days before it is due and
        updating the processing status.

        :return a count of total returns due.
        '''
        DUE_DAYS = 7
        verified = []
        today_plus_7 = date.today() + timedelta(days=DUE_DAYS)
        today = date.today()

        all_returns = Return.objects.filter(
            processing_status__in=[
                Return.RETURN_PROCESSING_STATUS_DRAFT,
                Return.RETURN_PROCESSING_STATUS_FUTURE,
                Return.RETURN_PROCESSING_STATUS_DUE,
                Return.RETURN_PROCESSING_STATUS_OVERDUE,
            ]
        )

        due_returns = all_returns.filter(
            due_date__range=[today, today_plus_7],
            processing_status__in=[
                Return.RETURN_PROCESSING_STATUS_DRAFT,
                Return.RETURN_PROCESSING_STATUS_FUTURE
            ]
        )
        status = Return.RETURN_PROCESSING_STATUS_DUE
        for a_return in due_returns:
            if not for_all and not a_return.id == id:
                continue
            # set future species list for return before setting status.
            utils = ReturnSpeciesUtility(a_return)
            licence_activity_id = a_return.condition.licence_activity_id
            selected_activity = [
                a for a in a_return.application.activities
                if a.licence_activity_id == licence_activity_id
            ][0]
            raw_specie_names = utils.get_raw_species_list_for(
                selected_activity
            )
            utils.set_species_list_future(raw_specie_names)
            # update status for the return.
            a_return.set_processing_status(status)
            verified.append(a_return)

        overdue_returns = all_returns.filter(
            due_date__lt=today,
            processing_status__in=[
                Return.RETURN_PROCESSING_STATUS_DRAFT,
                Return.RETURN_PROCESSING_STATUS_FUTURE,
                Return.RETURN_PROCESSING_STATUS_DUE
            ]
        ).exclude(
            return_type__data_format=ReturnType.FORMAT_SHEET
        )
        status = Return.RETURN_PROCESSING_STATUS_OVERDUE
        for a_return in overdue_returns:
            if not for_all and not a_return.id == id:
                continue
            a_return.set_processing_status(status)

        expired_returns = all_returns.filter(
            due_date__lt=today,
            processing_status__in=[
                Return.RETURN_PROCESSING_STATUS_DRAFT,
                Return.RETURN_PROCESSING_STATUS_FUTURE,
                Return.RETURN_PROCESSING_STATUS_DUE,
                Return.RETURN_PROCESSING_STATUS_OVERDUE,
            ],
            return_type__data_format=ReturnType.FORMAT_SHEET
        )
        status = Return.RETURN_PROCESSING_STATUS_EXPIRED
        for a_return in expired_returns:
            if not for_all and not a_return.id == id:
                continue
            # Expired Running Sheets have a 14 day grace period before the
            # status changes to Expired. Allows for final updates when not
            # renewing.
            # NOTE: At renewal the stock totals are aggregated for the newly
            # generated return. The old one is then discarded.
            expired_date = a_return.due_date + timedelta(days=14)
            expired_plus_14 = [
                a_return.due_date + datetime.timedelta(n)
                for n in range(int((expired_date - a_return.due_date).days))
            ]
            if today in expired_plus_14:
                continue

            a_return.set_processing_status(status)

        return verified

    @staticmethod
    def get_details_for(a_return):
        """
        Return data presented in table format with column headers.
        :return: formatted data.
        """
        logger.debug('ReturnService.get_details_for() - start')
        details = []
        try:
            if a_return.has_sheet:
                sheet = ReturnSheet(a_return)
                details = sheet.table

            if a_return.has_data:
                data = ReturnData(a_return)
                details = data.table

            if a_return.has_question:
                question = ReturnQuestion(a_return)
                details = question.table

        except BaseException as e:
            # NOTE: invalid schema exception can be thrown here.
            logger.error('get_details_for() ID {0} - {1}'.format(
                a_return.id, e
            ))
        logger.debug('ReturnService.get_details_for() - end')

        return details

    @staticmethod
    def store_request_details_for(a_return, request):
        """
        Return data presented in table format with column headers.
        :return: formatted data.
        """
        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            sheet.store(request)

        if a_return.has_data:
            data = ReturnData(a_return)
            data.store(request)

        if a_return.has_question:
            question = ReturnQuestion(a_return)
            question.store(request)

        fee = ReturnService.calculate_fees(a_return)
        a_return.set_return_fee(fee['fees']['return'])
        return []

    @staticmethod
    def validate_sheet_transfer_for(a_return, request):
        '''
        Validates the transfer details of stock on a Return running sheet.
        '''
        is_valid = False
        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            is_valid = sheet.is_valid_transfer(request)

        return is_valid

    @staticmethod
    def get_sheet_activity_list_for(a_return):

        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            return sheet.activity_list

        return None

    @staticmethod
    def get_sheet_species_list_for(a_return):
        '''
        Get list of species available for the return.
        '''
        logger.debug('ReturnService.get_sheet_species_list_for() - start')
        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            return sheet.species_list

        return None

    @staticmethod
    def get_sheet_species_saved_for(a_return):
        '''
        Get list of species saved for the return.
        '''
        logger.debug('ReturnService.get_sheet_species_saved_for() - start')
        saved_list = None
        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            saved_list = sheet.get_species_saved()
        logger.debug('ReturnService.get_sheet_species_saved_for() - end')

        return saved_list

    @staticmethod
    def get_sheet_species_for(a_return):

        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            return sheet.species

        return None

    @staticmethod
    def get_species_list_for(a_return):
        '''
        Get list of species available for the return.
        '''
        logger.debug('ReturnService.get_species_list_for() - start')
        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            return sheet.species_list

        if a_return.has_data:
            data = ReturnData(a_return)
            return data.species_list

        return None

    @staticmethod
    def set_species_for(a_return, species_id):

        updated = None

        if a_return.has_sheet:
            updated = ReturnSheet(a_return)
            updated.set_species(species_id)

        if a_return.has_data:
            updated = ReturnData(a_return)
            updated.set_species(species_id)

        return updated

    @staticmethod
    def get_species_for(a_return):

        if a_return.has_sheet:
            sheet = ReturnSheet(a_return)
            return sheet.species

        if a_return.has_data:
            data = ReturnData(a_return)
            return data.species

        return None


class ReturnFactory(object):
    '''
    An Abstract Factory interface that declares a method to create a Return.
    '''

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def create_return(self, request, licence, selected_activity) -> Return:
        '''
        Method to create a Return.

        :param: request is an incoming client request.
        :param: licence is a WildlifeLicence.
        :param: selected_activity is a ApplicationSelectedActivity.
        '''
        pass


@singleton
class ReturnGenerator(ReturnFactory):
    '''
    A spcialised ReturnFactory to generate a Return of different variants ie.
    ReturnSheet, ReturnData, ReturnQuestion. Guarantees resulting products are
    compatible.
    '''

    def __init__(self):
        pass

    def create_return(self, request, licence, selected_activity) -> Return:
        '''
        Method to create a Return.

        NOTE: Will create multiple Return depending on Application Conditions
        and return the last compliancy Return created.

        :param: request is an incoming client request.
        :param: licence is a WildlifeLicence.
        :param: selected_activity is a ApplicationSelectedActivity.

        :return: the_return the last compliancy Return created.
        '''
        import six
        from wildlifecompliance.components.applications.models import (
            ApplicationCondition,
        )
        FUTURE = Return.RETURN_PROCESSING_STATUS_FUTURE
        DRAFT = Return.RETURN_PROCESSING_STATUS_DRAFT
        DUE = Return.RETURN_PROCESSING_STATUS_DUE
        OVERDUE = Return.RETURN_PROCESSING_STATUS_OVERDUE
        DISCARD = Return.RETURN_PROCESSING_STATUS_DISCARDED

        WEEKLY = ApplicationCondition.APPLICATION_CONDITION_RECURRENCE_WEEKLY
        MONTHLY = ApplicationCondition.APPLICATION_CONDITION_RECURRENCE_MONTHLY
        YEARLY = ApplicationCondition.APPLICATION_CONDITION_RECURRENCE_YEARLY

        prev_ret = []

        def do_create_return(condition, a_date):
            '''
            An internal function to create the first return.

            :param condition is an Application Condition with Return Type.
            :param a_date is the due_date expected for the created return.

            :return first_return set to Draft for immediate update.
            '''
            already_generated = False

            try:
                # NOTE: Must be unique application conditions on the selected
                # activity otherwise first return not created.
                first_return = Return.objects.get(
                    condition=condition, due_date=a_date)
                already_generated = True

            except Return.DoesNotExist:
                first_return = Return.objects.create(
                    application=selected_activity.application,
                    due_date=a_date,
                    processing_status=DRAFT,
                    licence=licence,
                    condition=condition,
                    return_type=condition.return_type,
                )

            # Make first return editable (draft) for applicant but cannot
            # submit until due. Establish species list for first return.
            first_return.save()
            returns_utils = ReturnSpeciesUtility(first_return)

            # raw_specie_names is a list of names defined manually by the
            # licensing officer at the time of propose/issuance.
            raw_specie_names = returns_utils.get_raw_species_list_for(
                selected_activity
            )
            if not already_generated:
                returns_utils.set_species_list(raw_specie_names)

            # When first return generated is for a renewed application, discard
            # previous returns which are draft, due or overdue.
            if first_return.is_renewed():
                prev_app = selected_activity.application.previous_application
                prev_ret = prev_app.returns_application.all()

                c = condition
                do_discard_return(condition, prev_ret)
                discard_returns = [
                    r for r in prev_ret
                    if r.condition and r.condition.licence_activity == c.licence_activity
                    and r.condition.licence_purpose == c.licence_purpose
                    and r.condition.return_type == c.return_type
                    and r.condition.condition_text == c.condition_text
                    # and r.processing_status in [DISCARD]
                ]

                # When first Return is a Running Sheet copy discarded data.
                # ie. retain stock total.
                if first_return.has_sheet:

                    c = first_return.condition
                    returns = [
                        r for r in discard_returns
                        if r.condition.condition_text == c.condition_text
                    ]
                    if returns:
                        util = ReturnSpeciesUtility(first_return)
                        util.copy_sheet_species(returns[0])

            # log action
            if not already_generated:
                first_return.log_user_action(
                    ReturnUserAction.ACTION_CREATE.format(
                        first_return.lodgement_number,
                        first_return.condition.condition,
                        first_return.condition.licence_activity.short_name,
                    ), request
                )

            return first_return

        def do_amend_return(condition, amend_return_list):
            '''
            An internal function to amend a previously created return.

            :param Condition is an Application Condition with Return Type.
            :return Return that was amended.
            '''
            amended = None

            previous_returns = [
                r for r in amend_return_list
                if r.condition.licence_activity == condition.licence_activity
                and r.condition.licence_purpose == condition.licence_purpose
                and r.condition.return_type == condition.return_type
                # and r.condition.due_date == condition.due_date
                and r.condition.condition_text == condition.condition_text
            ]   # previous returns include Future ones.

            for previous in previous_returns:
                previous.application = selected_activity.application
                previous.condition = condition
                previous.save()
                if (previous.processing_status == DRAFT):
                    amended = previous

            return amended

        def do_discard_return(condition, return_list):
            '''
            An internal function to discard a previously created return.

            :param Condition is an Application Condition with Return Type.
            :return Return that was amended.
            '''
            discarded = False

            discardable = [
                r for r in return_list
                if r.condition and r.condition.licence_activity == condition.licence_activity
                and r.condition.licence_purpose == condition.licence_purpose
                and r.condition.return_type == condition.return_type
                and r.condition.condition_text == condition.condition_text
                # and r.condition.due_date == condition.due_date
            ]   # previous returns include Future ones.

            for r in discardable:
                discarded = True
                command = DiscardRequestCommand(request, condition, r)
                command.execute()

            return discarded

        def do_create_return_recurrence(condition, a_date):
            '''
            An internal function to create FUTURE Return.

            :param condition is an Application Condition with Return Type.
            :param a_date is the due_date expected for the created return.
            '''
            # Set the recurrences as future returns.
            # NOTE: species list will be determined and built when the
            # return is due.
            a_return = None
            if condition.recurrence:

                while a_date < licence_expiry:
                    # set the due date for recurrence period.
                    for x in range(condition.recurrence_schedule):
                        # Weekly
                        if condition.recurrence_pattern == WEEKLY:
                            a_date += timedelta(weeks=1)
                        # Monthly
                        elif condition.recurrence_pattern == MONTHLY:
                            a_date += timedelta(weeks=4)
                        # Yearly
                        elif condition.recurrence_pattern == YEARLY:
                            a_date += timedelta(days=365)

                        if a_date <= licence_expiry:
                            # Create the Return.
                            try:
                                a_return = Return.objects.get(
                                    condition=condition, due_date=a_date)

                            except Return.DoesNotExist:
                                a_return = Return.objects.create(
                                    application=selected_activity.application,
                                    due_date=a_date,
                                    processing_status=FUTURE,
                                    licence=licence,
                                    condition=condition,
                                    return_type=condition.return_type,
                                )

            return a_return

        '''
        Returns are generated at issuing; expiry_date may not be set yet.
        correct expiry is on the licence purpose.
        '''
        try:
            the_return = None
            licence_expiry = selected_activity.get_expiry_date()
            licence_expiry = datetime.datetime.strptime(
                licence_expiry, "%Y-%m-%d"
            ).date() if isinstance(
                licence_expiry, six.string_types
            ) else licence_expiry
            today = timezone.now().date()
            timedelta = datetime.timedelta

            excl_purpose = []
            if selected_activity.application.is_amendment():
                prev_app = selected_activity.application.previous_application
                prev_ret = prev_app.returns_application.exclude(
                    processing_status=DISCARD,
                )

                # discard previous returns for ApplicationConditions which have
                # been removed from the Amendment Application.
                act_id = selected_activity.licence_activity_id
                prev_conditions = [
                    r.condition for r in prev_ret.filter(
                        condition__licence_activity_id=act_id
                    )
                ]
                prev_conditions_ids = [
                    c.standard_condition_id for c in prev_conditions
                ]

                next_conditions = [
                    c for c in selected_activity.application.conditions.filter(
                        licence_activity_id=act_id
                    ).exclude(
                        return_type=None
                    )
                ]
                next_conditions_ids = [
                    c.standard_condition_id for c in next_conditions
                ]

                discard = set(prev_conditions_ids) - set(next_conditions_ids)
                discardable = [
                    c for c in prev_conditions
                    if c.standard_condition_id in list(discard)
                ]
                for condition in discardable:
                    do_discard_return(condition, prev_ret)

            # create or amend Return for each Condition.
            for condition in selected_activity.get_condition_list():

                if condition.return_type and condition.due_date \
                        and condition.due_date >= today:

                    current_date = condition.due_date
                    the_return = None
                    if selected_activity.application.is_amendment():
                        the_return = do_amend_return(condition, prev_ret)

                    if not the_return:
                        the_return = do_create_return(condition, current_date)
                        do_create_return_recurrence(condition, current_date)

                    excl_purpose.append(condition.licence_purpose)

            # discard/delete previous Returns from removed Conditions.
            if selected_activity.application.is_amendment():

                la = selected_activity.licence_activity
                discardable = [     # a subset excluding amended Returns.
                    r for r in prev_ret
                    if r.condition.licence_purpose not in excl_purpose
                    and r.condition.licence_activity == la
                    and r.processing_status in [DUE, OVERDUE, DRAFT]
                ]

                for r in discardable:
                    command = DiscardRequestCommand(request, r.condition, r)
                    command.execute()

        except Exception as e:
            logger.error('{0} {1} - {2}'.format(
                'ReturnService.generate_return_request() ActivityID:',
                selected_activity,
                e
            ))
            raise

        return the_return


class ReturnETL(object):
    '''
    A context maintaining a reference for a ReturnETL strategy.
    '''
    strategy = None                     # composite strategy.

    def __init__(self, strategy):
        self.strategy = strategy

    def process(self):
        '''
        Method to execute the strategy.
        '''
        self.strategy.do_algorithm()


class ReturnETLStrategy(object):
    '''
    An interface for ReturnETL strategies.
    '''
    LOGFILE = 'logs/etl_tasks.log'
    logger_title = 'ReturnService.ETL()'

    __metaclass__ = abc.ABCMeta

    @abc.abstractclassmethod
    def do_algorithm(self):
        '''
        Excutes the routine for this strategy.
        '''
        pass


class CleanseReturnSheet(ReturnETLStrategy):
    '''
    A real-time ReturnETLStrategy to remove dirty Return running sheets.

    NOTE: Output is not logged but printed. Apply pipe tee statement to log.
    '''
    return_ids = None                   # list of specific returns.

    def __init__(self, real_time, returns=None):
        self.return_ids = returns
        self.real_time = real_time

    def do_algorithm(self):
        '''
        Process each Return running sheet ensuring data integrity.
        '''
        import datetime
        log = '{0} {1} {2}'.format(
            datetime.datetime.now(), self.logger_title, 'Commencing cleansing.'
        )
        print(log)

        returns = Return.objects.filter(
            return_type__data_format=ReturnType.FORMAT_SHEET
        )

        if self.return_ids:         # filter returns for specific ids.
            returns = [r for r in returns if r.id in self.return_ids]

        duplicate_cnt = 0
        doa_cnt = 0

        for r in returns:
            utils = ReturnSpeciesUtility(r)
            for specie in r.return_type.regulated_species.all():
                name = utils.get_id_from_species_name(specie.species_name)
                try:
                    tables = [t for t in r.returntable_set.filter(name=name)]

                except AttributeError:
                    continue

                first = tables[0]

                '''
                1. Remove any duplicate species existing in tables.
                '''
                for idx, t in enumerate(tables, start=0):
                    if idx == 0:
                        continue
                    log = '{0} ReturnID: {1} {2} ReturnTableID: {3}'.format(
                        self.logger_title,
                        t.ret_id,
                        'Deleted duplicate species table.',
                        t.id,
                    )
                    duplicate_cnt += 1
                    if self.real_time:
                        print(log)
                        t.delete()

                '''
                2. Default the Date of Activity to the Date of Entry.
                '''
                for r in first.returnrow_set.all():
                    updated = False
                    doa = datetime.datetime.fromtimestamp(
                        r.data['date'] / 1000).strftime('%d/%m/%Y')
                    try:
                        if r.data['doa'] == '':
                            r.data['doa'] = doa
                            updated = True

                    except KeyError:
                        r.data['doa'] = doa
                        updated = True

                    if updated:
                        log = '{0} ReturnID: {1} {2} ReturnRowID: {3}'.format(
                            self.logger_title,
                            first.ret_id,
                            'Added Date of Activity.',
                            r.id,
                        )
                        doa_cnt += 1
                        if self.real_time:
                            print(log)
                            r.save()

        log = '{0} {1} {2}'.format(
            datetime.datetime.now(), self.logger_title, 'Completed cleansing.'
        )
        print(log)
        log = '{0} {1} {2}'.format(
            self.logger_title, 'Total Deleted', duplicate_cnt
        )
        print(log)
        log = '{0} {1} {2}'.format(
            self.logger_title, 'Total DOA added', doa_cnt
        )
        print(log)


class ReturnCommand(object):
    '''
    Declares an interface common to all supported Return client requests.

    '''
    request = None                      # property for client request.
    the_return = None                   # property for the Return.
    user_action = None                  # property for the logging action.

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def execute(self):
        '''
        Method to perfom an operation on the Return.
        '''
        pass

    def log_action(self):
        '''
        Method to log this command action.
        '''
        self.the_return.log_user_action(
            self.user_action.format(
                self.the_return.lodgement_number,
                self.the_return.condition.condition,
                self.the_return.condition.licence_activity.short_name,
            ), self.request
        )


class DiscardRequestCommand(ReturnCommand):
    '''
    A ReturnCommand to execute the discarding process of a Return and to log
    the Action.
    '''
    condition = None            # property to descard at condition level.

    def __init__(self, request, condition, a_return=None):
        self.request = request
        self.condition = condition
        self.the_return = a_return

    def __str__(self):
        return 'DiscardRequestCommand() CondID: {0}'.format(self.condition.id)

    def execute(self):
        '''
        Concrete method.
        '''
        # 1. get all returns for the condition.
        if self.the_return:
            returns = Return.objects.filter(id=self.the_return.id)
        else:
            returns = Return.objects.filter(condition=self.condition)

        # 2  set discard
        discardable = returns.exclude(
            processing_status=Return.RETURN_PROCESSING_STATUS_FUTURE
        )
        discardable.update(
            processing_status=Return.RETURN_PROCESSING_STATUS_DISCARDED
        )

        # 3. delete all future returns.
        future = returns.filter(
            processing_status=Return.RETURN_PROCESSING_STATUS_FUTURE
        )
        future.delete()

        # 4. log action.
        self.user_action = ReturnUserAction.ACTION_DISCARD
        for a_return in discardable:
            self.the_return = a_return
            self.log_action()


'''
NOTE: This section for objects relating to Specialised Returns.
'''


class ReturnData(object):
    """
    Informational data of requirements supporting licence condition.
    """
    def __init__(self, a_return):
        self._return = a_return

        self._species_list = []
        self._table = {'data': None}
        # build list of currently added Species.
        self._species = None
        for _species in ReturnTable.objects.filter(ret=a_return):
            self._species_list.append(_species.name)
            self._species = _species.name

    @property
    def table(self):
        """
        Table of return information presented in Grid format.
        :return: Grid formatted data.
        """
        tables = []
        for resource in self._return.return_type.resources:
            resource_name = resource.get('name')
            schema = Schema(resource.get('schema'))
            headers = []
            for f in schema.fields:
                header = {
                    "label": f.data['label'],
                    "name": f.data['name'],
                    "required": f.required,
                    "type": f.type.name,
                    "readonly": False,
                }
                if f.is_species:
                    header["species"] = f.species_type
                headers.append(header)
            table = {
                'name': resource_name,
                'label': resource.get('title', resource.get('name')),
                'type': 'grid',
                'headers': headers,
                'data': None
            }
            try:
                if self.requires_species():
                    resource_name = self._species

                return_table = self._return.returntable_set.get(
                    name=resource_name)
                all_return_rows = return_table.returnrow_set.all()
                rows = [
                    return_row.data for return_row in all_return_rows]

                if not rows:
                    raise ReturnTable.DoesNotExist()

                validated_rows = schema.rows_validator(rows)
                table['data'] = validated_rows
            except ReturnTable.DoesNotExist:
                result = {}
                results = []
                for field_name in schema.fields:
                    result[field_name.name] = {
                            'value': None
                    }
                results.append(result)
                table['data'] = results
            tables.append(table)

        return tables

    @property
    def species(self):
        """
        Species type associated with this Return Data.
        :return:
        """
        return self._species

    @property
    def species_list(self):
        """
        List of Species available with Return Data.
        :return: List of Species.
        {
         'S000001': 'Western Grey Kangaroo', 'S000002': 'Western Red Kangaroo',
         'S000003': 'Blue Banded Bee', 'S000004': 'Orange-Browed Resin Bee'
        }

        """
        new_list = {}
        for _species in ReturnTable.objects.filter(ret=self._return):
            utils = ReturnSpeciesUtility(self._return)
            name_str = utils.get_species_name_from_id(_species.name)
            new_list[_species.name] = name_str

            self._species = _species.name

        self._species_list.append(new_list)

        return new_list

    def _species_list(self):
        """
        List of Species available with Return Data.
        :return: List of Species.
        {
         'S000001': 'Western Grey Kangaroo', 'S000002': 'Western Red Kangaroo',
         'S000003': 'Blue Banded Bee', 'S000004': 'Orange-Browed Resin Bee'
        }

        """
        from wildlifecompliance.components.licences.models import (
            LicenceSpecies
        )
        new_list = {}
        for _species in ReturnTable.objects.filter(ret=self._return):
            try:
                lic_specie = LicenceSpecies.objects.filter(
                    specie_id=int(_species.name)
                )

            except BaseException as e:
                logger.error('species_list() ID: {0} - {1}'.format(
                    self._return.id,
                    e,
                ))

            lic_specie_data = lic_specie[0].data
            lic_specie_name = lic_specie_data[0]['vernacular_names']
            value = lic_specie_name
            new_list[_species.name] = value
            self._species = _species.name

        self._species_list.append(new_list)
        return new_list

    def store(self, request):
        """
        Save the current state of this Return Data.
        :param request:
        :return:
        """
        if not request.data.get('table_name'):
            return

        returns_tables = request.data.get('table_name')
        table_deficiency = returns_tables + '-deficiency-field'

        def _validate_and_save_key_data(key, data):
            '''
            Validate and Save data.
            '''
            if key == "nilYes":
                self._return.nil_return = True
                self._return.comments = request.data.get('nilReason')
                self._return.save()

            elif key == "nilNo":
                # Not submitting a Nil return so save data.
                is_valid_data = self._is_post_data_valid(
                    # returns_tables.encode('utf-8'),
                    returns_tables,
                    data
                )
                if is_valid_data:

                    # table_info = returns_tables.encode('utf-8')
                    table_info = returns_tables
                    if self._return.return_type.with_no_species:
                        table_rows = self._get_table_rows(table_info, data)
                        if table_rows:
                            self._return.save_return_table(
                                table_info, table_rows, request
                            )

                    else:
                        for species in self.species_list:
                            try:
                                species_data = data[species]

                            except KeyError:
                                continue

                            table_rows = self._get_table_species_rows(
                                species,
                                species_data
                            )
                            table_info = species

                            if table_rows:
                                self._return.save_return_table(
                                    table_info, table_rows, request
                                )
                else:
                    raise FieldError('Enter data in correct format.')

            elif key == table_deficiency:
                # table_info = returns_tables.encode('utf-8')
                table_info = returns_tables
                table_rows = self._get_table_rows(
                    table_info, data)
                if self.requires_species():
                    table_info = self._species
                    # table_rows = None
                if table_rows:
                    self._return.save_return_table(
                        table_info, table_rows, request)

        # def _parse_species_data(data):
        #     '''
        #     parse species data for storing.
        #     '''
        #     import json

        #     _parsed_data = request.data
        #     _json_data = json.loads(data)

        #     for _data in _json_data:
        #         for _key in _data.keys():
        #             try:
        #                 _value = _data[_key]['value']
        #                 _key_name = '{0}::{1}'.format(returns_tables, _key)
        #                 _parsed_data[_key_name] = _value

        #             except KeyError:
        #                 pass

        #     return _parsed_data

        for key in request.data.keys():
            data = request.data

            # if key in self._species_list:
            #     parsed_data = _parse_species_data(request.data[key])
            #     self.set_species(key)
            #     data = parsed_data
            #     key = "nilNo"

            _validate_and_save_key_data(key, data)

    def get_species_list(self):
        '''
        List of Species available with Return Data.
        :return: List of Species.
        {
         'S000001': 'Western Grey Kangaroo', 'S000002': 'Western Red Kangaroo',
         'S000003': 'Blue Banded Bee', 'S000004': 'Orange-Browed Resin Bee'
        }

        '''
        new_list = {}
        for _species in ReturnTable.objects.filter(ret=self._return):
            utils = ReturnSpeciesUtility(self._return)
            name_str = utils.get_species_name_from_id(_species.name)
            new_list[_species.name] = name_str

            self._species = _species.name

        self._species_list.append(new_list)

        return new_list

    def get_table_deficiency(self, deficiency_key):
        '''
        Get deficiency added for this return data.
        '''
        deficiency = None

        try:
            row = self.table[0]['data'].gi_frame.f_locals['rows'][0]
            deficiency = row[deficiency_key]

        except BaseException:
            pass

        return deficiency

    def set_table_deficiency(self, rows):
        '''
        Set deficiency added for this return data.
        '''
        try:
            table_name = self._return.return_type.resources[0]['name']
            deficiency_key = table_name + '-deficiency-field'

            table_deficiency = self.get_table_deficiency(deficiency_key)
            for row in rows:
                row[deficiency_key] = table_deficiency

        except BaseException as e:
            logger.error('ERR: set_table_deficiency : {0}'.format(e))

        return True

    def build_table(self, rows):
        """
        Method to create and validate rows of data to the table schema without
        persisting. Used for Loading data from spreadsheets.
        :param rows: data to be formatted.
        :return: Array of tables.
        """
        tables = []

        # retain deficiencies when building.
        self.set_table_deficiency(rows)

        for resource in self._return.return_type.resources:
            resource_name = resource.get('name')
            schema = Schema(resource.get('schema'))
            table = {
                'name': resource_name,
                'label': resource.get('title', resource.get('name')),
                'type': None,
                'headers': None,
                'data': None
            }
            try:
                validated_rows = schema.rows_validator(rows)
                table['data'] = validated_rows
            except AttributeError:
                result = {}
                results = []
                for field_name in schema.fields:
                    result[field_name.name] = {
                            'value': None
                    }
                results.append(result)
                table['data'] = results
            tables.append(table)

        return tables

    def _is_post_data_valid(self, tables_info, post_data):
        """
        Validates table data against the Schema for correct entry of data
        types.
        :param tables_info:
        :param post_data:
        :return:
        """
        table_rows = self._get_table_rows(tables_info, post_data)
        if len(table_rows) == 0:
            return False
        schema = Schema(
            self._return.return_type.get_schema_by_name(tables_info))
        if not schema.is_all_valid(table_rows):
            return False
        return True

    def _get_table_species_rows(self, species, species_data):
        """
        Builds a row of data taken from a table into a standard that can be
        consumed by the Schema.
        :param species:
        :param post_data:
        :return:
        """
        import json

        rows = []
        _json_data = json.loads(species_data)

        for _data in _json_data:
            for key in _data.keys():
                try:
                    value = _data[key]['value']
                except KeyError:
                    continue
                _data[key] = value
            rows.append(_data)

        return rows

    def _get_table_rows(self, table_name, post_data):
        """
        Builds a row of data taken from a table into a standard that can be
        consumed by the Schema.
        :param table_name:
        :param post_data:
        :return:
        """
        from django.utils.datastructures import MultiValueDictKeyError

        table_namespace = table_name + '::'
        by_column = dict([(key.replace(table_namespace, ''), post_data.getlist(
            key)) for key in post_data.keys() if key.startswith(
                table_namespace)])
        # by_column is of format {'col_header':[row1_val, row2_val,...],...}
        num_rows = len(
            list(
                by_column.values())[0]) if len(
            by_column.values()) > 0 else 0
        rows = []
        for row_num in range(num_rows):
            row_data = {}
            for key, value in by_column.items():
                row_data[key] = value[row_num]
            # filter empty rows.
            is_empty = True
            for value in row_data.values():
                if len(value.strip()) > 0:
                    is_empty = False
                    break
            if not is_empty:
                deficiency_data = post_data['table_name'] + '-deficiency-field'
                try:
                    # test if deficiency exists and include in row_data.
                    row_data[deficiency_data] = post_data[deficiency_data]
                except MultiValueDictKeyError:
                    pass
                rows.append(row_data)
        return rows

    def requires_species(self):
        '''
        A check to determine if this return type contains a list of species.
        '''
        return self._return.has_species_list

    def set_species(self, _species):
        """
        Sets the species for the current return data.
        :param _species:
        :return:
        """
        self._species = _species
        # self._species_list.add(_species)

    def get_species(self):
        """
        Gets the species for the current return data.
        :return:
        """
        return self._species

    def get_species_saved(self):
        '''
        Getter for saved species on the Return for this Return Data.
        {
         'S000001': 'Western Grey Kangaroo', 'S000002': 'Western Red Kangaroo',
         'S000003': 'Blue Banded Bee', 'S000004': 'Orange-Browed Resin Bee'
        }
        :return: list of species saved on the return.
        '''
        logger.debug('ReturnData.get_species_saved() - start')
        new_list = {}

        return new_list

    def __str__(self):
        return self._return.lodgement_number


class ReturnActivityFacade(object):
    """
    An Activity relating to the Transfer of Stock.
    """

    _TRANSFER_STATUS_NONE = ''
    _TRANSFER_STATUS_NOTIFY = 'Notified'
    _TRANSFER_STATUS_ACCEPT = 'Accepted'
    _TRANSFER_STATUS_DECLINE = 'Declined'

    # Activity properties.
    _ACTIVITY_DATE = 'date'
    _COMMENT = 'comment'
    _TRANSFER = 'transfer'
    _QUANTITY = 'qty'
    _LICENCE = 'licence'
    _ACTIVITY = 'activity'
    _TOTAL = 'total'
    _ROWID = 'rowId'

    def __init__(self, transfer):
        self.date = transfer[self._ACTIVITY_DATE]
        self.comment = transfer[self._COMMENT]
        self.transfer = transfer[self._TRANSFER]
        self.qty = transfer[self._QUANTITY]
        self.licence = transfer[self._LICENCE]
        self.total = ''
        self.rowId = '0'
        self.activity = transfer[self._ACTIVITY]

    def get_licence_return(self):
        """
        Method to retrieve Return with Running Sheet from a Licence No.
        :return: a Return object.
        """
        try:
            return Return.objects.filter(
                licence__licence_number=self.licence,
                return_type__data_format=ReturnType.FORMAT_SHEET
                ).first()

        except Return.DoesNotExist:
            raise ValidationError({'error': 'Error exception.'})

    @staticmethod
    def factory(transfer):
        NOTIFY = ReturnActivityFacade._TRANSFER_STATUS_NOTIFY
        ACCEPT = ReturnActivityFacade._TRANSFER_STATUS_ACCEPT
        DECLINE = ReturnActivityFacade._TRANSFER_STATUS_DECLINE

        if transfer[ReturnActivityFacade._TRANSFER] == NOTIFY:
            return NotifyTransfer(transfer)
        if transfer[ReturnActivityFacade._TRANSFER] == ACCEPT:
            return AcceptTransfer(transfer)
        if transfer[ReturnActivityFacade._TRANSFER] == DECLINE:
            return DeclineTransfer(transfer)

        return None


class NotifyTransfer(ReturnActivityFacade):
    """
    Notification of a Transfer Activity.
    """

    def __init__(self, transfer):
        super(NotifyTransfer, self).__init__(transfer)
        self.activity = ReturnSheet.ACTIVITY_OPTIONS[
            transfer[self._ACTIVITY]]['outward']

    @transaction.atomic
    def store_transfer_activity(self, species, request, from_return):
        """
        Saves the Transfer Activity under the Receiving Licence return for
        species.
        :return: _new_transfer boolean.
        """
        to_return = self.get_licence_return()
        self.licence = from_return.licence.licence_number

        try:
            # get the Return Table record and save immediately to check if it
            # has been concurrently modified.
            return_table, created = ReturnTable.objects.get_or_create(
                name=species, ret=to_return)
            return_table.save()
            rows = ReturnRow.objects.filter(return_table=return_table)
            table_rows = []
            row_exists = False
            total = 0
            row_cnt = 0
            self.rowId = str(row_cnt)
            for row in rows:
                if row.data[self._ACTIVITY_DATE] == self.date:  # update record
                    row_exists = True
                    row.data[self._QUANTITY] = self.qty
                    row.data[self._COMMENT] = self.comment
                    row.data[self._TRANSFER] = self.transfer
                total = row.data[self._TOTAL]
                table_rows.append(row.data)
                row_cnt = row_cnt + 1
                self.rowId = str(row_cnt)
            if not row_exists:
                self.total = total
                table_rows.append(self.__dict__)
            # delete any existing rows as they will all be recreated
            return_table.returnrow_set.all().delete()
            return_rows = [
                ReturnRow(
                    return_table=return_table,
                    data=row) for row in table_rows]
            ReturnRow.objects.bulk_create(return_rows)
            # log transaction
            from_return.log_user_action(
                ReturnUserAction.ACTION_SUBMIT_TRANSFER.format(
                    from_return), request)

            if not row_exists:
                send_sheet_transfer_email_notification(
                    request, to_return, from_return)

            return row_exists
        except RecordModifiedError:
            raise IntegrityError(
                'A concurrent save occurred please refresh page details.')
        except BaseException:
            raise


class AcceptTransfer(ReturnActivityFacade):
    """
    A ReturnActivityFacade that is an Accepted Transfer.
    """

    def __init__(self, transfer):
        super(AcceptTransfer, self).__init__(transfer)

    @transaction.atomic
    def store_transfer_activity(self, species, request, from_return):
        """
        Saves the Transfer Activity under the Receiving Licence return for
        species.
        :return: _new_transfer boolean.
        """
        to_return = self.get_licence_return()

        try:
            # get the Return Table record and save immediately to check if
            # it has been concurrently modified.
            return_table = ReturnTable.objects.get(name=species, ret=to_return)
            return_table.save()
            rows = ReturnRow.objects.filter(return_table=return_table)
            table_rows = []
            row_exists = False
            for row in rows:  # update total and status for accepted activity.
                if row.data[self._ACTIVITY_DATE] == self.date:
                    row_exists = True
                    row.data[self._TRANSFER] = \
                        ReturnActivityFacade._TRANSFER_STATUS_ACCEPT
                    row.data[
                        self._TOTAL] = int(row.data[
                            self._TOTAL]) - int(self.qty)
                    break
            for row in rows:  # update totals for subsequent activities.
                if row_exists and int(row.data[
                        self._ACTIVITY_DATE]) > int(self.date):
                    row.data[self._TOTAL] = int(row.data[
                        self._TOTAL]) - int(self.qty)
                table_rows.append(row.data)
            # delete any existing rows as they will all be recreated
            return_table.returnrow_set.all().delete()
            return_rows = [
                ReturnRow(
                    return_table=return_table,
                    data=row) for row in table_rows]
            ReturnRow.objects.bulk_create(return_rows)
            # log transaction
            from_return.log_user_action(
                ReturnUserAction.ACTION_ACCEPT_TRANSFER.format(
                    from_return), request)

            return row_exists
        except RecordModifiedError:
            raise IntegrityError(
                'A concurrent save occurred please refresh page details.')
        except BaseException:
            raise


class DeclineTransfer(ReturnActivityFacade):
    """
    A ReturnActivityFacade that is an Declined Transfer.
    """

    def __init__(self, transfer):
        super(DeclineTransfer, self).__init__(transfer)

    @transaction.atomic
    def store_transfer_activity(self, species, request, from_return):
        """
        Saves the Transfer Activity under the Receiving Licence return for
        species.
        :return: _new_transfer boolean.
        """
        to_return = self.get_licence_return()

        try:
            # get the Return Table record and save immediately to check if it
            # has been concurrently modified.
            return_table = ReturnTable.objects.get(name=species, ret=to_return)
            return_table.save()
            rows = ReturnRow.objects.filter(return_table=return_table)
            table_rows = []
            row_exists = False
            for row in rows:  # update status for selected activity.
                if row.data[self._ACTIVITY_DATE] == self.date:
                    row_exists = True
                    row.data[self._TRANSFER] = \
                        ReturnActivityFacade._TRANSFER_STATUS_DECLINE
                table_rows.append(row.data)

            # delete any existing rows as they will all be recreated
            return_table.returnrow_set.all().delete()
            return_rows = [
                ReturnRow(
                    return_table=return_table,
                    data=row) for row in table_rows]
            ReturnRow.objects.bulk_create(return_rows)
            # log transaction
            from_return.log_user_action(
                ReturnUserAction.ACTION_DECLINE_TRANSFER.format(
                    from_return), request)

            return row_exists
        except RecordModifiedError:
            raise IntegrityError(
                'A concurrent save occurred please refresh page details.')
        except BaseException:
            raise


class ReturnQuestion(object):
    """
    Informational question of requirements supporting licence condition.
    """
    def __init__(self, a_return):
        self._return = a_return

    @property
    def table(self):
        """
        Table of return questions.
        :return: formatted data.
        """
        tables = []
        for resource in self._return.return_type.resources:
            resource_name = ReturnType.FORMAT_QUESTION
            schema = Schema(resource.get('schema'))
            headers = []
            for f in schema.fields:
                header = {
                    "label": f.data['label'],
                    "name": f.data['name'],
                    "required": f.required,
                    "type": f.type.name,
                    "readonly": False,
                }
                if f.is_species:
                    header["species"] = f.species_type
                headers.append(header)
            table = {
                'name': resource_name,
                'title': resource.get('title', resource.get('name')),
                'headers': headers,
                'data': None
            }
            try:
                r_table = self._return.returntable_set.get(
                    name=resource_name)
                rows = [
                    r_row.data for r_row in r_table.returnrow_set.all()]
                table['data'] = rows
            except ReturnTable.DoesNotExist:
                result = {}
                results = []
                for field_name in schema.fields:
                    result[field_name.name] = {
                        'value': None
                    }
                results.append(result)
                table['data'] = results
            tables.append(table)
        return tables

    def store(self, request):
        """
        Save the current state of the Return.
        :param request:
        :return:
        """
        # Nb: There is only ONE row where each Question is a header.
        table_rows = self._get_table_rows(request.data)
        self._return.save_return_table(
            ReturnType.FORMAT_QUESTION, table_rows, request)

    def _get_table_rows(self, _data):
        """
        Builds a row of data taken from the Request into a standard that can
        be saved.
        :param _data:
        :return:
        """
        # by_column is of format {'col_header':[row1_val, row2_val,...],...}
        by_column = dict([])
        rows = []
        for key in _data.keys():
            by_column[key] = _data[key]
        rows.append(by_column)

        return rows

    def __str__(self):
        return self._return.lodgement_number


class ReturnSheet(object):
    """
    Informational Running Sheet of Species requirements supporting licence
    condition.
    """
    _DEFAULT_SPECIES = '0000000'

    _SHEET_SCHEMA = {
        "name": "sheet",
        "title": "Running Sheet of Return Data",
        "resources": [{
            "name": "species_id",
            "path": "",
            "title": "Return Data for Specie",
            "schema": {
                "fields": [{
                    "name": "date",
                    "type": "date",
                    "format": "fmt:%d/%m/%Y",
                    "constraints": {
                        "required": True}
                    }, {
                    "name": "activity",
                    "type": "string",
                    "constraints": {
                        "required": True}
                    }, {
                    "name": "doa",
                    "type": "date",
                    "format": "fmt:%d/%m/%Y",
                    "constraints": {
                        "required": True}
                    }, {
                    "name": "qty",
                    "type": "number",
                    "constraints": {
                        "required": True}
                    }, {
                    "name": "total",
                    "type": "number",
                    "constraints": {
                        "required": True}
                    }, {
                    "name": "licence",
                    "type": "string"
                    }, {
                    "name": "comment",
                    "type": "string"
                    }, {
                    "name": "supplier",
                    "type": "string"
                    }, {
                    "name": "transfer",
                    "type": "string"
                    }
                ]
            }}]}

    _NO_ACTIVITY = {
        "echo": 1,
        "totalRecords": "0",
        "totalDisplayRecords": "0",
        "data": []}

    SA01 = ReturnActivity.TYPE_IN_STOCK
    SA02 = ReturnActivity.TYPE_IN_ACQUISITION
    SA03 = ReturnActivity.TYPE_IN_BIRTH
    SA04 = ReturnActivity.TYPE_IN_TRANSFER
    SA05 = ReturnActivity.TYPE_OUT_DISPOSAL
    SA06 = ReturnActivity.TYPE_OUT_DEATH
    SA07 = ReturnActivity.TYPE_OUT_OTHER
    SA08 = ReturnActivity.TYPE_OUT_DEALER
    NONE = "0"      # allow for blank row on default.

    SA01_TEXT = ReturnActivity.TYPE_DESC.get(SA01)
    SA02_TEXT = ReturnActivity.TYPE_DESC.get(SA02)
    SA03_TEXT = ReturnActivity.TYPE_DESC.get(SA03)
    SA04_TEXT = ReturnActivity.TYPE_DESC.get(SA04)
    SA05_TEXT = ReturnActivity.TYPE_DESC.get(SA05)
    SA06_TEXT = ReturnActivity.TYPE_DESC.get(SA06)
    SA07_TEXT = ReturnActivity.TYPE_DESC.get(SA07)
    SA08_TEXT = ReturnActivity.TYPE_DESC.get(SA08)

    ACTIVITY_OPTIONS = {
        SA01: {"label": SA01_TEXT, "auto": "false", "licence": "false",
               "pay": "false", "initial": ""},
        SA02: {"label": SA02_TEXT, "auto": "false",
               "licence": "false", "pay": "false", "inward": ""},
        SA03: {"label": SA03_TEXT, "auto": "false",
               "licence": "false", "pay": "false", "inward": ""},
        # SA04: {"label": SA04_TEXT, "auto": "true",
        #        "licence": "false", "pay": "false", "inward": ""},
        SA05: {"label": SA05_TEXT, "auto": "false",
               "licence": "false", "pay": "false", "outward": ""},
        SA06: {"label": SA06_TEXT, "auto": "false",
               "licence": "false", "pay": "false", "outward": ""},
        # SA07: {"label": SA07_TEXT, "auto": "false",
        #        "licence": "true", "pay": "true", "outward": SA04},
        # SA08: {"label": SA08_TEXT, "auto": "false",
        #        "licence": "true", "pay": "false", "outward": SA04},
        NONE: {"label": "", "auto": "false", "licence": "false",
               "pay": "false", "initial": ""}
    }

    _return = None                  # Composite Return.
    _species_list = None            # List of Species available.
    _table = {'data': None}         # Table of Return details.
    _species = None                 # Selected saved Specie.
    _species_saved = []             # List of Species saved.

    def __init__(self, a_return):
        logger.debug('ReturnSheet.__init__() - start')
        self._return = a_return
        self._return.return_type.data_descriptor = self._SHEET_SCHEMA
        self._species_list = []
        self._table = {'data': None}
        # build list of currently added Species.
        self._species = None
        self._species_list = ReturnTable.objects.filter(ret=a_return)
        # self._species_list.append(_species.name)
        # if (_species.has_rows()):
        #     self._species_saved.append(_species.name)
        #     self._species = _species.name
        self.get_species_list()
        logger.debug('ReturnSheet.__init__() - end')

    # @staticmethod
    # def set_licence_species(the_return):
    #     """
    #     Sets the species from the licence for the current Running Sheet.
    #     :return:
    #     """
    #     # TODO: create default entries for each species on the licence.
    #     # TODO: Each species has a defaulted Stock Activity (0 Totals).
    #     # TODO: Call _set_activity_from_previous to carry over Stock totals
    #     # for Licence reissues.
    #     '''
    #     _data = []
    #     new_sheet = the_return.sheet
    #     for species in the_return.licence.species_list:
    #         try:
    #             _data = {''}
    #             table_rows = new_sheet._get_table_rows(_data)
    #             self._return.save_return_table(species, table_rows, request)
    #         except AttributeError:
    #             continue
    #     '''
    #     pass

    @property
    def table(self):
        """
        Running Sheet Table of data for Species. Defaults to a Species on the
        Return if exists.
        :return: formatted data.
        """
        return self._get_activity(self._species)['data']

    @property
    def species(self):
        """
        Species type associated with this Running Sheet of Activities.
        :return:
        """
        return self._species

    @property
    def species_list(self):
        '''
        Property list of species available on this return sheet.
        '''
        # return self.get_species_list()
        logger.debug('ReturnSheet.species_list() - count {}'.format(
            len(self._species_list)
        ))
        return self.get_species_list()

    @property
    def activity_list(self):
        """
        List of stock movement activities applicable for Running Sheet.
        Format: "SA01": {
            "label": "Stock",
            "auto": "false",
            "licence": "false",
            "pay": "false",
            "outward": "SA04"}
        Label: Activity Description.
        Auto: Flag indicating automated activity.
        Licence: Flag indicating licence required for activity.
        Pay: Flag indicating payment required for activity.
        Inward/Outward: Transfer type with Activity Type for outward transfer.
        :return: List of Activities applicable for Running Sheet.
        """
        return self.ACTIVITY_OPTIONS

    # todo: more generic method name for payment transfer
    def process_transfer_fee_payment(self, request):
        '''
        Process transfer fees.

        NOTE: redundant.
        '''
        from ledger.payments.models import BpointToken
        # if self.return_ee_paid:
        #    return True

        application = self.application
        applicant = application.proxy_applicant \
            if application.proxy_applicant else application.submitter
        card_owner_id = applicant.id
        card_token = BpointToken.objects.filter(
            user_id=card_owner_id).order_by('-id').first()
        if not card_token:
            logger.error("No card token found for user: %s" % card_owner_id)
            return False

        product_lines = []
        return_submission = u'Transfer of stock for {} Return {}'.format(
            u'{} {}'.format(applicant.first_name, applicant.last_name),
            application.lodgement_number)
        oracle_code = self._return.return_type.oracle_account_code
        product_lines.append({
            'ledger_description': '{}'.format(self._return.id),
            'quantity': 1,
            'price_incl_tax': str(self._return.return_fee),
            'price_excl_tax': str(calculate_excl_gst(self.licence_fee)),
            'oracle_code': oracle_code
        })
        checkout(
            request, application, lines=product_lines,
            invoice_text=return_submission,
            internal=True,
            add_checkout_params={
                'basket_owner': request.user.id,
                'payment_method': 'card',
                'checkout_token': card_token.id,
            }
        )
        try:
            invoice_ref = request.session['checkout_invoice']
        except KeyError:
            ID = self.licence_activity_id
            logger.error(
                "No invoice reference generated for Activity ID: %s" % ID)
            return False
        ReturnInvoice.objects.get_or_create(
            invoice_return=self,
            invoice_reference=invoice_ref
        )
        flush_checkout_session(request.session)
        # return self.licence_fee_paid and
        # send_activity_invoice_email_notification(
        # application, self, invoice_ref, request)
        return self.licence_fee_paid

    def store(self, request):
        """
        Save the current state of this Return Sheet.
        :param request:
        :return:
        """
        for species in self.species_list:
            _data = request.data.get(species)

            if not _data:
                continue

            try:
                # _data = request.data.get(species).encode('utf-8')
                _data = ast.literal_eval(_data)  # ast should convert to tuple.
                table_rows = self._get_table_rows(_data)
                self._return.save_return_table(species, table_rows, request)

            except AttributeError as e:
                logger.info('ReturnSheet.store() ID: {0} {1} - {2}'.format(
                    self._return.id, species, e
                ))
                continue

        self._add_transfer_activity(request)

    def set_species(self, _species):
        """
        Sets the species for the current Running Sheet.
        :param _species:
        :return:
        """
        self._species = _species
        # self._species_list.add(_species)

    def get_species(self):
        """
        Gets the species for the current Running Sheet.
        :return:
        """
        return self._species

    def get_species_saved(self):
        '''
        Getter for saved species on the Return for this sheet.
        {
         'S000001': 'Western Grey Kangaroo', 'S000002': 'Western Red Kangaroo',
         'S000003': 'Blue Banded Bee', 'S000004': 'Orange-Browed Resin Bee'
        }
        :return: list of species saved on the return.
        '''
        logger.debug('ReturnSheet.get_species_saved() - start')
        new_list = {}
        util = ReturnSpeciesUtility(self._return)
        ordered = self._species_list.order_by('name')
        for _species in ordered:
            if (_species.has_rows()):
                name_str = util.get_species_name_from_id(_species.name)
                new_list[_species.name] = name_str

        self._species_saved.append(new_list)
        logger.debug('ReturnSheet.get_species_saved() - end')

        return new_list

    def get_species_list(self):
        '''
        Getter for species available on the Return for this sheet.
        {
         'S000001': 'Western Grey Kangaroo', 'S000002': 'Western Red Kangaroo',
         'S000003': 'Blue Banded Bee', 'S000004': 'Orange-Browed Resin Bee'
        }
        :return: list of species available on the return.
        '''
        logger.debug('ReturnSheet.get_species_list() - start')
        available_list = {}

        util = ReturnSpeciesUtility(self._return)
        for _species in self._species_list:
            self._species = _species.name
            if (_species.has_rows()):
                self._species = _species.name
                break
        name_str = util.get_species_name_from_id(self._species)
        available_list[self._species] = name_str

        for _species in self._species_list:
            name_str = util.get_species_name_from_id(_species.name)
            available_list[_species.name] = name_str
            # if _species.name != self._species:
            #     name_str = util.get_species_name_from_id(_species.name)
            #     available_list[_species.name] = name_str

        logger.debug('ReturnSheet.get_species_list() - end')
        return available_list

    def get_species_list_from_tsc(self):
        '''
        Getter for species available on the Return for this sheet. The species
        are taken from TSC server (redundant).
        {
         'S000001': 'Western Grey Kangaroo', 'S000002': 'Western Red Kangaroo',
         'S000003': 'Blue Banded Bee', 'S000004': 'Orange-Browed Resin Bee'
        }
        :return: List of Species.
        '''
        from wildlifecompliance.components.licences.models import (
            LicenceSpecies
        )
        new_list = {}
        for _species in ReturnTable.objects.filter(ret=self._return):

            lic_specie = LicenceSpecies.objects.filter(
                specie_id=int(_species.name)
            )
            lic_specie_data = lic_specie[0].data
            lic_specie_name = lic_specie_data[0]['vernacular_names']
            _species_detail = ReturnRow.objects.filter(return_table=_species)
            if _species_detail.exists():
                value = lic_specie_name
                new_list[_species.name] = value
                self._species = _species.name
        self._species_list.append(new_list)
        return new_list

    def is_valid_transfer(self, req):
        """
        Validate transfer request details.
        :param request:
        :return:
        """
        is_valid = True                             # applying fuzzy logic.

        if not req.data.get('transfer'):
            return False

        # _data = req.data.get('transfer').encode('utf-8')
        _data = req.data.get('transfer')
        _transfers = ast.literal_eval(_data)
        _lic = _transfers['licence']

        is_valid = \
            False if not is_valid else self._is_valid_transfer_licence(_lic)

        is_valid = \
            False if not is_valid else self._is_valid_transfer_quantity(req)

        return is_valid

    def _get_activity(self, _species_id):
        """
        Get Running Sheet activity for the movement of Species stock.
        :return:
        formatted data {
            'name': 'speciesId',
            'data': [{'date': '2019/01/23', 'activity': 'SA01', ..., }]}
        """
        self._species = _species_id
        for resource in self._return.return_type.resources:
            _resource_name = _species_id
            _schema = Schema(resource.get('schema'))
            try:
                _r_table = self._return.returntable_set.get(
                    name=_resource_name)
                rows = [
                    _r_row.data for _r_row in _r_table.returnrow_set.all()
                ]
                _schema.set_field_for(rows)     # Add missing schema fields.
                _schema.rows_validator(rows)
                self._table['data'] = rows
                self._table['echo'] = 1
                self._table['totalRecords'] = str(rows.__len__())
                self._table['totalDisplayRecords'] = str(rows.__len__())
            except ReturnTable.DoesNotExist:
                self._table = self._NO_ACTIVITY

        return self._table

    def _get_table_rows(self, _data):
        """
        Gets the formatted row of data from Species data.
        :param _data:
        :return:
        """
        by_column = dict([])
        # by_column is of format {'col_header':[row1_val, row2_val,...],...}
        key_values = []
        num_rows = 0
        # if isinstance(_data, tuple):
        #     for key in _data[0].keys():
        #         for cnt in range(_data.__len__()):
        #             key_values.append(_data[cnt][key])
        #         by_column[key] = key_values
        #         key_values = []
        #     num_rows = len(list(by_column.values())[0])\
        #         if len(by_column.values()) > 0 else 0
        # else:
        #     for key in _data[0].keys():
        #         by_column[key] = _data[0][key]
        #     num_rows = num_rows + 1

        for key in _data[0].keys():
            for cnt in range(_data.__len__()):
                key_values.append(_data[cnt][key])
            by_column[key] = key_values
            key_values = []
        num_rows = len(list(by_column.values())[0])\
            if len(by_column.values()) > 0 else 0

        rows = []
        for row_num in range(num_rows):
            row_data = {}
            # if num_rows > 1:
            #     for key, value in by_column.items():
            #         row_data[key] = value[row_num]
            # else:
            #     row_data = by_column
            for key, value in by_column.items():
                row_data[key] = value[row_num]

            # filter empty rows.
            is_empty = True
            for value in row_data.values():
                if value and len(value.strip()) > 0:
                    is_empty = False
                    break
            if not is_empty:
                row_data['rowId'] = str(row_num)
                rows.append(row_data)

        return rows

    def _get_licence_return(self, licence_no):
        """
        Method to retrieve Return with Running Sheet from a Licence No.
        :param licence_no:
        :return: a Return object.
        """
        TYPE = ReturnType.FORMAT_SHEET
        try:
            return Return.objects.filter(licence__licence_number=licence_no,
                                         return_type__data_format=TYPE
                                         ).first()
        except Return.DoesNotExist:
            raise ValidationError({'error': 'Error exception.'})

    def _add_transfer_activity(self, request):
        """
        Add transfer activity to a validated receiving licence return.
        :param request:
        :return:
        """
        if not request.data.get('transfer'):
            return False
        # _data = request.data.get('transfer').encode('utf-8')
        _data = request.data.get('transfer')
        _transfers = ast.literal_eval(_data)
        if isinstance(_transfers, tuple):
            for transfer in _transfers:
                a_transfer = ReturnActivity.factory(transfer)
                a_transfer.store_transfer_activity(
                    transfer['species_id'], request, self._return)
        else:
            a_transfer = ReturnActivity.factory(_transfers)
            a_transfer.store_transfer_activity(
                _transfers['species_id'], request, self._return)

    def _is_valid_transfer_licence(self, _licence):
        """
        Method to check if licence is current.
        :return: boolean
        """
        return True if self._get_licence_return(_licence) else False

    def _is_valid_transfer_quantity(self, request):
        """
        Method to check transfer transfer quantity does not exceed total.
        :param request:
        :return: boolean
        """
        # TODO: This validation is not completed.
        if not request.data.get('transfer'):
            return False
        # data = request.data.get('transfer').encode('utf-8')
        data = request.data.get('transfer')
        ast.literal_eval(data)
        # quantity = transfers['qty']
        # species_id = transfers['transfer']
        '''
        return_table = ReturnTable.objects.get(
            name=species, ret=to_return)[0]
        rows = ReturnRow.objects.filter(return_table=return_table)
            # optimistic load of rows.
        table_rows = []
        r_exists = False
        total = 0
        for r in rows:  # update total and status for accepted activity.
            if r.data[self._ACTIVITY_DATE] == self.date:
                r_exists = True
                r.data[self._TRANSFER] = ReturnActivity._TRANSFER_STATUS_ACCEPT
                r.data[self._TOTAL] = int(r.data[self._TOTAL]) - int(self.qty)
                table_rows.append(r.data)
                break
        for r in rows:  # update totals for subsequent activities.
            if r_exists and int(r.data[self._ACTIVITY_DATE]) > int(self.date):
                r.data[self._TOTAL] = int(r.data[self._TOTAL]) - int(self.qty)
            table_rows.append(r.data)
        '''
        return True

    def __str__(self):
        return self._return.lodgement_number
