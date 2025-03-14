from django.contrib import admin
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from wildlifecompliance.components.artifact import models
from reversion.admin import VersionAdmin


@admin.register(models.Artifact)
class ArtifactAdmin(admin.ModelAdmin):
    pass

@admin.register(models.DocumentArtifact)
class DocumentArtifactAdmin(admin.ModelAdmin):
    raw_id_fields = ('statement','person_providing_statement',  'officer_interviewer', 'offence', 'offender')

@admin.register(models.PhysicalArtifact)
class PhysicalArtifactAdmin(admin.ModelAdmin):
    raw_id_fields = ('physical_artifact_type','officer',  'officer', 'custodian', 'disposal_method')

#@admin.register(models.DocumentArtifactType)
#class DocumentArtifactTypeAdmin(admin.ModelAdmin):
#    pass

@admin.register(models.PhysicalArtifactType)
class PhysicalArtifactTypeAdmin(admin.ModelAdmin):
    raw_id_fields = ('replaced_by',)

@admin.register(models.PhysicalArtifactDisposalMethod)
class PhysicalArtifactDisposalMethodAdmin(admin.ModelAdmin):
    pass

