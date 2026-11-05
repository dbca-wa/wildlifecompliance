import logging
import mimetypes

import six
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.urls import reverse
from django.template import loader, Template
from django.utils.html import strip_tags

from ledger_api_client.ledger_models import Document

from wagov_utils.components.utils.email import (
    TemplateEmailBase as WAGovUtilsTemplateEmailBase,
)

logger = logging.getLogger('log')

class TemplateEmailBase(WAGovUtilsTemplateEmailBase):
    subject = ''
    html_template = 'wildlifecompliance/emails/base_email.html'
    # txt_template can be None, in this case a 'tag-stripped' version of the
    # html will be sent. (see send)
    txt_template = 'wildlifecompliance/emails/base-email.txt'

class ExportReportEmail(TemplateEmailBase):
    
    def __init__(self,model_name=""):
        self.model_name = model_name
    
    model_name = ""
    subject='Attached: Wildlife Compliance - {} Report'.format(model_name.capitalize())
    html_template='wildlifecompliance/emails/report_attached.html'
    txt_template='wildlifecompliance/emails/report_attached.txt'