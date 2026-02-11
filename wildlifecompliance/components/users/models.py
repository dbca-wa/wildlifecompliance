from __future__ import unicode_literals
from django.db import models
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from wildlifecompliance.components.main.models import Document, Region, District #NOTE: Region and District needed here despite not being used (likely import issue)
from wildlifecompliance.components.main.models import SanitiseMixin

from django.conf import settings
from django.core.files.storage import FileSystemStorage
private_storage = FileSystemStorage(location=settings.BASE_DIR+"/private-media/", base_url='/private-media/')

class ComplianceManagementUserPreferences(SanitiseMixin):

    prefer_compliance_management = models.BooleanField(default=False)
    email_user = models.OneToOneField(EmailUser, on_delete=models.CASCADE)
    intelligence_information_text = models.TextField(blank=True)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Compliance Management User Preferences'

    def __str__(self):
        return '{}, {}'.format(self.email_user.id, self.prefer_compliance_management)


class ComplianceUserIntelligenceDocument(Document):
    email_user = models.ForeignKey(EmailUser, related_name='intelligence_documents', on_delete=models.CASCADE)
    _file = models.FileField(max_length=255,storage=private_storage)

    class Meta:
        app_label = 'wildlifecompliance'


import reversion
reversion.register(ComplianceManagementUserPreferences, follow=[])
reversion.register(ComplianceUserIntelligenceDocument, follow=[])