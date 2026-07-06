from django.contrib import admin
from ledger.accounts.models import EmailUser
from wildlifecompliance.components.legal_case import models
from reversion.admin import VersionAdmin


@admin.register(models.LegalCase)
class LegalCaseAdmin(admin.ModelAdmin):
    raw_id_fields = ('call_email', 'assigned_to', 'legal_case_priority')

@admin.register(models.LegalCasePriority)
class LegalCasePriorityAdmin(admin.ModelAdmin):
    pass

@admin.register(models.Court)
class CourtAdmin(admin.ModelAdmin):
    pass

@admin.register(models.CourtOutcomeType)
class CourtOutcomeTypeAdmin(admin.ModelAdmin):
    pass
