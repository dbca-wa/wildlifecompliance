from django.contrib import admin
from wildlifecompliance.components.licences.models import LicencePurpose
from wildlifecompliance.components.applications import models
from wildlifecompliance.components.applications import forms
from reversion.admin import VersionAdmin


class ApplicationDocumentInline(admin.TabularInline):
    model = models.ApplicationDocument
    extra = 0


@admin.register(models.AmendmentRequest)
class AmendmentRequestAdmin(admin.ModelAdmin):
    list_display = ['application', 'licence_activity']
    raw_id_fields = ('application', 'officer', 'licence_activity')


@admin.register(models.ApplicationSelectedActivity)
class ApplicationSelectedActivity(admin.ModelAdmin):
    raw_id_fields = ('application', 'licence_activity', 'updated_by', 'assigned_approver', 'assigned_officer')
    #pass


@admin.register(models.Assessment)
class Assessment(admin.ModelAdmin):
    raw_id_fields = ('application', 'officer', 'assessor_group', 'licence_activity', 'actioned_by', 'assigned_assessor')


@admin.register(models.ApplicationCondition)
class ApplicationCondition(admin.ModelAdmin):
    raw_id_fields = ('standard_condition', 'default_condition', 'application', 'licence_activity', 'return_type', 'licence_purpose', 'source_group')


@admin.register(models.DefaultCondition)
class DefaultCondition(admin.ModelAdmin):
    list_display = [
        'standard_condition',
        'licence_activity',
        'licence_purpose'
        ]
    raw_id_fields = ('standard_condition',  'licence_activity')


@admin.register(models.ActivityPermissionGroup)
class ActivityPermissionGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name']
    filter_horizontal = ('licence_activities',)
    form = forms.ActivityPermissionGroupAdminForm

    def has_delete_permission(self, request, obj=None):
        return super(
            ActivityPermissionGroupAdmin,
            self).has_delete_permission(
            request,
            obj)


class ApplicationInvoiceInline(admin.TabularInline):
    model = models.ApplicationInvoice
    extra = 0


@admin.register(models.Application)
class ApplicationAdmin(VersionAdmin):
    list_display = ['id', 'application_type', 'lodgement_number', 'lodgement_date']
    inlines = [ApplicationDocumentInline, ApplicationInvoiceInline]
    raw_id_fields = ('org_applicant','proxy_applicant','submitter',  'licence', 'licence_document', 'previous_application')


@admin.register(models.ApplicationStandardCondition)
class ApplicationStandardConditionAdmin(admin.ModelAdmin):
    list_display = ['id', 'code', 'short_description', 'obsolete']
    raw_id_fields = ('return_type',)

    def save_model(self, request, obj, form, change):
        obj.save(exclude_sanitise=["text"])


@admin.register(models.ApplicationSelectedActivityPurpose)
class ApplicationSelectedActivityPurposeAdmin(admin.ModelAdmin):
    list_display = ['id', 'purpose', 'purpose_status']
    raw_id_fields = ('selected_activity', 'purpose')

