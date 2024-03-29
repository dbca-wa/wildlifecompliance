from django.db import models
from django.db.models import Q

from ledger.accounts.models import RevisionedMixin


class Act(RevisionedMixin):
    NAME_CHOICES =  (
            ('BCA', 'Biodiversity Conservation Act 2016'),
            ('CALM', 'Conservation and Land Management Act 1984'),
            ('BCR', 'Biodiversity Conservation Regulations 2018'),
            ('CLMR', 'Conservation and Land Management Regulations 2002'),
            ('FMR', 'Forest Management Regulations 1993'),
            ('CIIPA', 'Criminal Investigation (Identifying People) Act 2006'),
            ('SCMRA', 'Swan and Canning Rivers Management Act 2006'),
            ('SCRMR', 'Swan and Canning Rivers Management Regulations 2007'),
            )

    name = models.CharField(max_length=50, choices=NAME_CHOICES)

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Act'
        verbose_name_plural = 'CM_Acts'

    def __str__(self):
        return self.name


class SectionRegulation(RevisionedMixin):
    #act = models.CharField(max_length=100, blank=True)
    act = models.ForeignKey(Act, related_name='section_regulations')
    name = models.CharField(max_length=50, blank=True, verbose_name='Regulation')
    offence_text = models.CharField(max_length=200, blank=True)
    is_parking_offence = models.BooleanField(default=False)
    dotag_offence_code = models.CharField(max_length=9, verbose_name='DotAG Offence Code', blank=True)

    # Officer can issue an infringement notice within this period after the offence occurrence date
    # If this is null, which means officer can issue the infringement notice anytime.
    issue_due_date_window =  models.PositiveSmallIntegerField(blank=True, null=True, help_text='An infringement notice must be issued within Issue-due-date-window days from the date of the offence occurred.')

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_Section/Regulation'
        verbose_name_plural = 'CM_Sections/Regulations'
        ordering = ('act', 'name')

    def retrieve_penalty_amounts_by_date(self, date_of_issue):
        return PenaltyAmount.objects.filter(
            Q(section_regulation=self) &
            Q(date_of_enforcement__lte=date_of_issue)).order_by('date_of_enforcement', ).last()

    def __str__(self):
        return '{}:{}:{}'.format(self.act, self.name, self.offence_text)


class PenaltyAmount(RevisionedMixin):
    amount = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    amount_after_due = models.DecimalField(max_digits=8, decimal_places=2, default='0.00')
    date_of_enforcement = models.DateField(blank=True, null=True)
    section_regulation = models.ForeignKey(SectionRegulation, related_name='penalty_amounts')

    class Meta:
        app_label = 'wildlifecompliance'
        verbose_name = 'CM_PenaltyAmount'
        verbose_name_plural = 'CM_PenaltyAmounts'
        ordering = ('date_of_enforcement', )  # oldest record first, latest record last

    def __str__(self):
        return '${} ({}:{})'.format(self.amount, self.date_of_enforcement, self.section_regulation)


import reversion
reversion.register(Act, follow=['section_regulations'])
reversion.register(SectionRegulation, follow=['penalty_amounts', 'offence_set', 'allegedoffence_set', 'sanction_outcome_alleged_offences'])
reversion.register(PenaltyAmount, follow=[])

