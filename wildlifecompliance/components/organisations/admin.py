from django.contrib import admin
from wildlifecompliance.components.organisations import models
# Register your models here.


@admin.register(models.Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    list_display = ['organisation_id']
    search_fields = ['organisation_id']


@admin.register(models.OrganisationRequest)
class OrganisationRequestAdmin(admin.ModelAdmin):
    raw_id_fields = ('requester', 'assigned_officer')
    list_display = ['id', 'name', 'lodgement_number', 'lodgement_date']
    search_fields = ['id', 'name', 'lodgement_number', 'lodgement_date']


@admin.register(models.OrganisationContact)
class OrganisationContactAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'user_role', 'organisation_id']
    raw_id_fields = ('organisation',)
    search_fields = ['first_name', 'last_name', 'user_role', 'organisation__organisation_id']


#@admin.register(models.UserDelegation)
#class UserDelegationAdmin(admin.ModelAdmin):
#    raw_id_fields = ('organisation', 'user')
#    list_display = ['organisation', 'user']


@admin.register(models.OrganisationAction)
class UOrganisationActionAdmin(admin.ModelAdmin):
    raw_id_fields = ('who', 'organisation')
