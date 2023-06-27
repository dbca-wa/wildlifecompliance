from django.contrib import admin
from ledger.accounts.models import EmailUser
from wildlifecompliance.components.inspection import models
from reversion.admin import VersionAdmin


@admin.register(models.Inspection)
class InspectionAdmin(admin.ModelAdmin):
    raw_id_fields = ('call_email', 'legal_case', 'location', 'individual_inspected', 'organisation_inspected', 'assigned_to', 'inspection_team_lead', 'inspection_type')

@admin.register(models.InspectionType)
class InspectionTypeAdmin(admin.ModelAdmin):
    raw_id_fields = ('replaced_by', 'approval_document')

@admin.register(models.InspectionTypeApprovalDocument)
class InspectionTypeApprovalDocumentAdmin(admin.ModelAdmin):
    pass
