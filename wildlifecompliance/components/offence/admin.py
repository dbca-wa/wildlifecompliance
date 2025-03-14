from django import forms
from django.contrib import admin
from reversion.admin import VersionAdmin

#import wildlifecompliance.components.section_regulation.models
from wildlifecompliance.components.offence import models
from wildlifecompliance.components.section_regulation.models import (
        PenaltyAmount, 
        SectionRegulation,
        Act,
        )


class PenaltyAmountInline(admin.TabularInline):
    model = PenaltyAmount
    extra = 0
    can_delete = True


@admin.register(models.Offence)
class OffenceAdmin(admin.ModelAdmin):
    #filter_horizontal = ('alleged_offences',)
    raw_id_fields = ('location', 'call_email', 'legal_case', 'inspection', 'assigned_to')


class SectionRegulationForm(forms.ModelForm):
    offence_text = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = SectionRegulation
        fields = '__all__'


class SectionRegulationAdmin(VersionAdmin):
    form = SectionRegulationForm
    inlines = [PenaltyAmountInline,]
    raw_id_fields = ('act',)
    # list_display = ['self', 'is_parking_offence', ]


@admin.register(PenaltyAmount)
class PenaltyAmountAdmin(admin.ModelAdmin):
    raw_id_fields = ('section_regulation',)

@admin.register(Act)
class ActAdmin(admin.ModelAdmin):
    pass


admin.site.register(SectionRegulation, SectionRegulationAdmin)

