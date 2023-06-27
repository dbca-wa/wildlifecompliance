from django.contrib import admin
from wildlifecompliance.components.organisations import models
# Register your models here.


@admin.register(models.Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    raw_id_fields = ('organisation',)


@admin.register(models.OrganisationRequest)
class OrganisationRequestAdmin(admin.ModelAdmin):
    raw_id_fields = ('requester', 'assigned_officer')
    list_display = ['id', 'name', 'lodgement_number', 'lodgement_date']


@admin.register(models.OrganisationContact)
class OrganisationContactAdmin(admin.ModelAdmin):
    raw_id_fields = ('organisation',)


@admin.register(models.UserDelegation)
class UserDelegationAdmin(admin.ModelAdmin):
    raw_id_fields = ('organisation', 'user')
    list_display = ['organisation', 'user']


@admin.register(models.OrganisationAction)
class UOrganisationActionAdmin(admin.ModelAdmin):
    raw_id_fields = ('who', 'organisation')
