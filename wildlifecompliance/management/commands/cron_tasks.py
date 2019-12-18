from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
import datetime

import subprocess

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run the Wildlife Compliance Cron tasks'

    def handle(self, *args, **options):
        logger.info('Running command {}'.format(__name__))

        subprocess.call('python manage_wc.py send_unpaid_infringements_file', shell=True)
        subprocess.call('python manage_wc.py extend_due_date_from_1st_to_2nd', shell=True)
        subprocess.call('python manage_wc.py send_rego_to_dot', shell=True)

        logger.info('Command {} completed'.format(__name__))