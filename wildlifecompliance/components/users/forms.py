from django.forms.models import ModelMultipleChoiceField
from django.contrib.admin.widgets import FilteredSelectMultiple


class GroupPermissionsField(ModelMultipleChoiceField):
    widget = FilteredSelectMultiple(verbose_name='Group Permissions / Roles', is_stacked=True)

def clean_email(self):
    return self.initial['email']
