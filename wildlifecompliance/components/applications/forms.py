from django import forms
from wildlifecompliance.components.applications.models import (
    ActivityPermissionGroup
)
from wildlifecompliance.components.main.models import WildlifeSystemPermission

from django.forms.models import ModelMultipleChoiceField
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db.models import Q

class GroupPermissionsField(ModelMultipleChoiceField):
    widget = FilteredSelectMultiple(verbose_name='Group Permissions / Roles', is_stacked=True)


class ActivityPermissionGroupAdminForm(forms.ModelForm):
    permissions = GroupPermissionsField(
        queryset=WildlifeSystemPermission.objects.filter(
           (Q(codename__startswith='wildlifecompliance.') & (Q(codename__endswith='activitypermissiongroup')|Q(codename__endswith='applicationgrouptype')))|
           Q(
               codename__in=[
                'wildlifecompliance.system_administrator',
                'wildlifecompliance.organisation_access_request',
                'wildlifecompliance.licensing_officer',
                'wildlifecompliance.issuing_officer',
                'wildlifecompliance.assessor',
                'wildlifecompliance.return_curator',
                'wildlifecompliance.payment_officer'
               ]
            )
        )
    )

    class Meta:
        model = ActivityPermissionGroup
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ActivityPermissionGroupAdminForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(ActivityPermissionGroupAdminForm, self).clean()


def clean_email(self):
    return self.initial['email']