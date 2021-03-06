import logging

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.core.urlresolvers import reverse
from django.conf import settings
from ledger.payments.pdf import create_invoice_pdf_bytes
from ledger.payments.models import Invoice
from wildlifecompliance.components.main.utils import get_choice_value
from wildlifecompliance.components.emails.emails import TemplateEmailBase
from wildlifecompliance.components.main.email import prepare_attachments, _extract_email_headers
import os

logger = logging.getLogger(__name__)

SYSTEM_NAME = 'Wildlife Licensing Automated Message'


class LegalCaseForwardNotificationEmail(TemplateEmailBase):
    subject = 'Forwarded Case'
    html_template = 'wildlifecompliance/emails/send_legal_case_forward_notification.html'
    txt_template = 'wildlifecompliance/emails/send_legal_case_forward_notification.txt'


def send_mail(select_group, legal_case, workflow_entry, request):
    email = LegalCaseForwardNotificationEmail()
    if request.data.get('email_subject'):
        email.subject = request.data.get('email_subject')
    url = request.build_absolute_uri(
        reverse(
            'internal-legal-case-detail',
            kwargs={
                'legal_case_id': legal_case.id
                }))
    context = {
        'url': url,
        'legal_case': legal_case,
        'workflow_entry_details': request.data.get('details'),
    }
    email_group = [item.email for item in select_group]
    attachments = prepare_attachments(workflow_entry.documents)
    msg = email.send(email_group, 
        context=context,
        attachments=attachments,
        )
    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    email_data = _extract_email_headers(msg, sender=sender)
    return email_data

