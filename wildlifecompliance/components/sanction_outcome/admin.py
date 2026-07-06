from django.contrib import admin

from wildlifecompliance.components.sanction_outcome.models import SanctionOutcome, AmendmentRequestReason
from wildlifecompliance.components.sanction_outcome_due.models import SanctionOutcomeDueDateConfiguration


@admin.register(SanctionOutcome)
class SanctionOutcomeAdmin(admin.ModelAdmin):
    filter_horizontal = ('alleged_offences',)
    raw_id_fields = ('offence', 'offender', 'assigned_to', 'responsible_officer', 'registration_holder', 'driver')


@admin.register(SanctionOutcomeDueDateConfiguration)
class SanctionOutcomeDueDateConfigurationAdmin(admin.ModelAdmin):
    pass


@admin.register(AmendmentRequestReason)
class AmendmentRequestReasonAdmin(admin.ModelAdmin):
    pass

