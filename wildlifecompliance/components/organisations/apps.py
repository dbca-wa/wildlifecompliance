from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrganisationsConfig(AppConfig):
    name = 'wildlifecompliance.components.organisations'
    verbose_name = _('organisations')

    def ready(self):
        import wildlifecompliance.components.organisations.signals
