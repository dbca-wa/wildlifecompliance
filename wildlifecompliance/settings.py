import os
import confy
import logging
from confy import env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
confy.read_environment_file(BASE_DIR+"/.env")
os.environ.setdefault("BASE_DIR", BASE_DIR)
from django.core.exceptions import ImproperlyConfigured
from ledger_api_client.settings_base import *


logger = logging.getLogger(__name__)

os.environ['LEDGER_PRODUCT_CUSTOM_FIELDS'] = "('ledger_description','quantity','price_incl_tax','price_excl_tax','oracle_code')"
os.environ['LEDGER_REFUND_TRANSACTION_CALLBACK_MODULE'] = 'wildlifecompliance:wildlifecompliance.components.applications.api.application_refund_callback'
os.environ['LEDGER_INVOICE_TRANSACTION_CALLBACK_MODULE'] = 'wildlifecompliance:wildlifecompliance.components.applications.api.application_invoice_callback'

ROOT_URLCONF = 'wildlifecompliance.urls'
SITE_ID = 1
SYSTEM_MAINTENANCE_WARNING = env('SYSTEM_MAINTENANCE_WARNING', 24)  # hours

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles_wc')
SHOW_DEBUG_TOOLBAR = env('SHOW_DEBUG_TOOLBAR', False)
APPEND_SOURCE_TO_RICHTEXT_ADMIN = env('APPEND_SOURCE_TO_RICHTEXT_ADMIN', False)
FILE_UPLOAD_MAX_MEMORY_SIZE = env('FILE_UPLOAD_MAX_MEMORY_SIZE', 2621440) # 2.5MB --> Django Default
STOP_SQL_LOG = env('STOP_SQL_LOG', False)
SHOW_ROOT_API = env('SHOW_ROOT_API', False)

LEDGER_UI_URL=env('LEDGER_UI_URL','')

SSO_SETTING_URL=env('SSO_SETTING_URL','')

TEMPLATE_TITLE = "Wildlife Licensing System"
TEMPLATE_HEADER_LOGO = "/static/wildlifecompliance/img/dbca-logo.png"
TEMPLATE_GROUP = "parkswildlifev2"

LEDGER_TEMPLATE = "bootstrap5"

WILDLIFECOMPLIANCE_EXTERNAL_URL = env('WILDLIFECOMPLIANCE_EXTERNAL_URL','External url not configured')

# Use git commit hash for purging cache in browser for deployment changes
GIT_COMMIT_HASH = os.popen(
    f"cd {BASE_DIR}; git log -1 --format=%H"
).read()  
GIT_COMMIT_DATE = os.popen(
    f"cd {BASE_DIR}; git log -1 --format=%cd"
).read()  
if len(GIT_COMMIT_HASH) == 0:
    GIT_COMMIT_HASH = os.popen("cat /app/git_hash").read()
APPLICATION_VERSION = env("APPLICATION_VERSION", "1.0.0") + "-" + GIT_COMMIT_HASH[:7]

if SHOW_DEBUG_TOOLBAR:
#    def get_ip():
#        import subprocess
#        route = subprocess.Popen(('ip', 'route'), stdout=subprocess.PIPE)
#        network = subprocess.check_output(
#            ('grep', '-Po', 'src \K[\d.]+\.'), stdin=route.stdout
#        ).decode().rstrip()
#        route.wait()
#        network_gateway = network + '1'
#        return network_gateway

    def show_toolbar(request):
        return True

    MIDDLEWARE_CLASSES += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
    INSTALLED_APPS += (
        'debug_toolbar',
    )
    #INTERNAL_IPS = ('127.0.0.1', 'localhost', get_ip())
    INTERNAL_IPS = ('127.0.0.1', 'localhost')

    # this dict removes check to dtermine if toolbar should display --> works for rks docker container
    DEBUG_TOOLBAR_CONFIG = {
        "SHOW_TOOLBAR_CALLBACK" : show_toolbar,
        'INTERCEPT_REDIRECTS': False,
    }

STATIC_URL = '/static/'

INSTALLED_APPS += [
    'reversion',
    'reversion_compare',
    'django.contrib.humanize',
    'wildlifecompliance',
    'wildlifecompliance.components.main',
    'wildlifecompliance.components.applications',
    'wildlifecompliance.components.organisations',
    'wildlifecompliance.components.licences',
    'wildlifecompliance.components.users',
    'wildlifecompliance.components.returns',
    'wildlifecompliance.components.call_email',
    'wildlifecompliance.components.offence',
    'wildlifecompliance.components.inspection',
    'wildlifecompliance.components.sanction_outcome',
    'wildlifecompliance.components.wc_payments',
    'wildlifecompliance.components.legal_case',
    'wildlifecompliance.components.artifact',
    'taggit',
    'rest_framework',
    'rest_framework_gis',
    'rest_framework_datatables',
    'smart_selects',
    'ckeditor',
    'appmonitor_client',
    'ledger_api_client',
    'webtemplate_dbca',
    'django_vite',
]

CKEDITOR_BASEPATH = '/static/ckeditor/ckeditor/'

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['RemoveFormat'],
            #[ 'Source']
        ]
    },
    'pdf_config': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            [ '-', 'Bold', 'Italic' ],
            [ 'Format' ],
            [ 'NumberedList', 'BulletedList' ],
            [ 'Table' ],
            #[ 'Source']
        ]
    },
}

if APPEND_SOURCE_TO_RICHTEXT_ADMIN:
    CKEDITOR_CONFIGS['pdf_config']['toolbar_Custom'].append(['Source'])


ADD_REVERSION_ADMIN = True

# maximum number of days allowed for a booking
WSGI_APPLICATION = 'wildlifecompliance.wsgi.application'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework_datatables.renderers.DatatablesRenderer',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'rest_framework_datatables.filters.DatatablesFilterBackend',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework_datatables.pagination.DatatablesPageNumberPagination',
    'PAGE_SIZE': 50,
}

USE_DJANGO_JQUERY=True

if env('EMAIL_INSTANCE') is not None and env('EMAIL_INSTANCE','') != 'PROD':
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += ('rest_framework.renderers.BrowsableAPIRenderer',)

MIDDLEWARE_CLASSES += [
    'wildlifecompliance.middleware.FirstTimeNagScreenMiddleware',
    'wildlifecompliance.middleware.CacheControlMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    #'django.contrib.sessions.middleware.SessionMiddleware',
    #'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'django.contrib.messages.middleware.MessageMiddleware',
    'wildlifecompliance.middleware.PaymentSessionMiddleware',
]

SESSION_ENGINE = 'django.contrib.sessions.backends.file'
if env('EMAIL_INSTANCE') is not None and env('EMAIL_INSTANCE','') != 'PROD':
    SESSION_FILE_PATH = env('SESSION_FILE_PATH', BASE_DIR+'/session_store/')
    if not os.path.isdir(SESSION_FILE_PATH):
        os.mkdir(SESSION_FILE_PATH)       
else:
    SESSION_FILE_PATH = env('SESSION_FILE_PATH', '/app/session_store/')

SESSION_COOKIE_SECURE = env('SESSION_COOKIE_SECURE', True)
CSRF_COOKIE_SECURE = env('CSRF_COOKIE_SECURE', True)
SESSION_COOKIE_AGE = env('SESSION_COOKIE_AGE',3600)

LEDGER_UI_CARDS_MANAGEMENT = True
LEDGER_UI_ACCOUNTS_MANAGEMENT = [
            # {'account_name': {'options' : {'view': True, 'edit': True}}},
            # {'legal_name': {'options' : {'view': True, 'edit': True}}},
            # {'verified_legal_name': {'options' : {'view': True, 'edit': True}}},

            {'first_name': {'options' : {'view': True, 'edit': True}}},
            {'last_name': {'options' : {'view': True, 'edit': True}}},
            {'legal_first_name': {'options' : {'view': True, 'edit': True}}},
            {'legal_last_name': {'options' : {'view': True, 'edit': True}}},
            {'dob': {'options' : {'view': True, 'edit': True}}},
 
            {'identification': {'options' : {'view': True, 'edit': True}}},

            {'residential_address': {'options' : {'view': True, 'edit': True}}},
            #{'postal_address': {'options' : {'view': True, 'edit': True}}},
            #{'postal_same_as_residential': {'options' : {'view': True, 'edit': True}}},

            #{'postal_address': {'options' : {'view': True, 'edit': True}}},
            {'phone_number' : {'options' : {'view': True, 'edit': True}}},
            {'mobile_number' : {'options' : {'view': True, 'edit': True}}},

]

ORGANISATION_PERMISSION_MODULE = 'wildlifecompliance.permission'

LEDGER_UI_ORGANISATION_MANAGEMENT = [
        {'organisation_name': {'options' : {'view': True, 'edit': True}}},
        {'organisation_abn': {'options' : {'view': True, 'edit': True}}},
        {'postal_address': {'options' : {'view': True, 'edit': True}}}
]

LEDGER_UI_ACCOUNTS_MANAGEMENT_KEYS = []
for am in LEDGER_UI_ACCOUNTS_MANAGEMENT:
    LEDGER_UI_ACCOUNTS_MANAGEMENT_KEYS.append(list(am.keys())[0])

LEDGER_SYSTEM_ID = env('PAYMENT_INTERFACE_SYSTEM_PROJECT_CODE', 'PAYMENT_INTERFACE_SYSTEM_PROJECT_CODE not configured')
PAYMENT_SYSTEM_ID = LEDGER_SYSTEM_ID.replace('0', 'S')

LATEX_GRAPHIC_FOLDER = os.path.join(BASE_DIR,"templates","latex","images")

TEMPLATES[0]['DIRS'].append(
    os.path.join(
        BASE_DIR,
        'wildlifecompliance',
        'templates'))
TEMPLATES[0]['DIRS'].append(
    os.path.join(
        BASE_DIR,
        'wildlifecompliance',
        'components',
        'organisations',
        'templates'))
TEMPLATES[0]['DIRS'].append(
    os.path.join(
        BASE_DIR,
        'wildlifecompliance',
        'components',
        'emails',
        'templates'))

TEMPLATES[0]["OPTIONS"]["context_processors"].append(
    "wildlifecompliance.context_processors.authorised_index"
)
TEMPLATES[0]["OPTIONS"]["context_processors"].append('wildlifecompliance.context_processors.wildlifecompliance_processor')

CACHE_TIMEOUT_2_HOURS = 60 * 60 * 2
CACHE_KEY_FILE_EXTENSION_WHITELIST = "file-extension-whitelist"
FILE_SIZE_LIMIT_BYTES = env('FILE_SIZE_LIMIT_BYTES' ,128000000)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'wildlifecompliance', 'cache'),
    }
}
CRON_CLASSES = [
    'wildlifecompliance.cron.OracleIntegrationCronJob',
]

# Add a new formatter
LOGGING['formatters']['verbose2'] = {
    "format": "%(levelname)s %(asctime)s %(name)s [Line:%(lineno)s][%(funcName)s] %(message)s"
}
LOGGING['handlers']['console']['formatter'] = 'verbose2'
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['handlers']['file']['formatter'] = 'verbose2'
# Additional logging for wildlifecompliance
LOGGING['handlers']['application_checkout'] = {
    'level': 'INFO',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': os.path.join(
        BASE_DIR,
        'logs',
        'wildlifecompliance_application_checkout.log'),
    'formatter': 'verbose',
    'maxBytes': 5242880}
LOGGING['loggers']['application_checkout'] = {
    'handlers': ['application_checkout'],
    'level': 'INFO'
}
# Additional logging for securebase manager.
LOGGING['handlers']['securebase_manager'] = {
    'level': 'INFO',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': os.path.join(
        BASE_DIR,
        'logs',
        'securebase_manager.log'),
    'formatter': 'verbose',
    'maxBytes': 5242880}
LOGGING['loggers']['securebase_manager'] = {
    'handlers': ['securebase_manager'],
    'level': 'INFO'
}
LOGGING['loggers']['']['level'] = 'DEBUG'
LOGGING['loggers']['wildlifecompliance'] = {
    "handlers": [ "console", "file" ],
    "level": "DEBUG",
    "propagate": False  # Prevent double logging by stopping propagation
}
if not STOP_SQL_LOG:
    LOGGING['handlers']['file_sql'] = {
        'level': 'DEBUG',
        'class': 'logging.handlers.RotatingFileHandler',
        'filename': os.path.join(
            BASE_DIR,
            'logs',
            'sql.log'),
        'formatter': 'verbose2',
        'maxBytes': 5242880   
    }
    LOGGING['loggers']['django.db.backends'] = {
        'handlers': ['file_sql'],
        'level': 'DEBUG',
        'propagate': False
    }

STATICFILES_DIRS.append(os.path.join(BASE_DIR, 'wildlifecompliance', 'static'))
STATICFILES_DIRS.append(os.path.join(BASE_DIR, 'wildlifecompliance', 'static', 'wildlifecompliance_vue'))

DATA_UPLOAD_MAX_NUMBER_FIELDS = None

# Department details
SYSTEM_NAME = env('SYSTEM_NAME', 'Wildlife Licensing System')
WILDCARE_SYSTEM_NAME = env('WILDCARE_SYSTEM_NAME', 'Wildcare')
SYSTEM_EMAIL = env('SYSTEM_EMAIL', 'wildlifelicensing@dbca.wa.gov.au')

WC_PAYMENT_SYSTEM_ID = env('WC_PAYMENT_SYSTEM_ID', 'S566')
WC_PAYMENT_SYSTEM_PREFIX = env('PAYMENT_SYSTEM_PREFIX', WC_PAYMENT_SYSTEM_ID.replace('S', '0'))
PS_PAYMENT_SYSTEM_ID = WC_PAYMENT_SYSTEM_ID
WC_PAYMENT_SYSTEM_URL_PDF = env('WC_PAYMENT_SYSTEM_URL_PDF', '/ledger-toolkit-api/invoice-pdf/')
WC_PAYMENT_SYSTEM_URL_INV = env('WC_PAYMENT_SYSTEM_URL_INV', '/ledger/payments/invoice/')
WC_PAY_INFR_URL = env('WC_PAY_INFR_URL','https://www.google.com')

COLS_ADMIN_GROUP = env('COLS_ADMIN_GROUP', 'COLS Admin')
if not VALID_SYSTEMS:
    VALID_SYSTEMS = [WC_PAYMENT_SYSTEM_ID]
DEP_URL = env('DEP_URL', 'www.dbca.wa.gov.au')
DEP_PHONE = env('DEP_PHONE', '(08) 9219 9831')
DEP_FAX = env('DEP_FAX', '(08) 9423 8242')
DEP_POSTAL = env(
    'DEP_POSTAL',
    'Locked Bag 104, Bentley Delivery Centre, Western Australia 6983')
DEP_NAME = env(
    'DEP_NAME',
    'Department of Biodiversity, Conservation and Attractions')
DEPT_DOMAINS = env('DEPT_DOMAINS', ['dpaw.wa.gov.au', 'dbca.wa.gov.au'])
SITE_PREFIX = env('SITE_PREFIX')
SITE_DOMAIN = env('SITE_DOMAIN')
SITE_URL = env('SITE_URL', 'https://' + SITE_PREFIX + '.' + SITE_DOMAIN)
SITE_URL_WLC = env('SITE_URL_WLC')
GROUP_PREFIX = env('GROUP_PREFIX', 'Wildlife Compliance')
COMPLIANCE_GROUP_PREFIX = env('COMPLIANCE_GROUP_PREFIX', 'Compliance Management')
EXT_USER_API_ROOT_URL = env('EXT_USER_API_ROOT_URL', None)
EXCEL_OUTPUT_PATH = env('EXCEL_OUTPUT_PATH')
ALLOW_EMAIL_ADMINS = env('ALLOW_EMAIL_ADMINS', False)  # Allows internal pages to be accessed via email authentication
SYSTEM_APP_LABEL = env('SYSTEM_APP_LABEL', 'wildlifecompliance')  # global app_label for group permissions filtering
RENEWAL_PERIOD_DAYS = env('RENEWAL_PERIOD_DAYS', 30)
GEOCODING_ADDRESS_SEARCH_TOKEN = env('GEOCODING_ADDRESS_SEARCH_TOKEN', 'ACCESS_TOKEN_NOT_FOUND')
DOT_EMAIL_ADDRESS = env('DOT_EMAIL_ADDRESS')

SUPER_AUTH_GROUPS_ENABLED = env('SUPER_AUTH_GROUPS_ENABLED',False) #allows officers (or equivalent group type) without specified region access all regions, and officers without specified district to access all districts within a specified region
AUTH_GROUP_REGION_DISTRICT_LOCK_ENABLED = env('AUTH_GROUP_REGION_DISTRICT_LOCK_ENABLED',False) #restricts officers (or equivalent group type) to only their specified region/district (with exceptions if SUPER_AUTH_GROUPS_ENABLED)

# Details for Threathened Species and Communities server.
TSC_URL = env('TSC_URL', 'https://tsc.dbca.wa.gov.au')
TSC_AUTH = env('TSC_AUTH', 'NO_AUTH')
CRON_RUN_AT_TIMES = env('CRON_RUN_AT_TIMES', '02:05')

if env('CONSOLE_EMAIL_BACKEND', False):
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
# if DEBUG:
#     EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
#

SO_TYPE_INFRINGEMENT_NOTICE = 'infringement_notice'
SO_TYPE_CAUTION_NOTICE = 'caution_notice'
SO_TYPE_LETTER_OF_ADVICE = 'letter_of_advice'
SO_TYPE_REMEDIATION_NOTICE = 'remediation_notice'

SO_TYPE_CHOICES = (
    (SO_TYPE_INFRINGEMENT_NOTICE, 'Infringement Notice'),
    (SO_TYPE_CAUTION_NOTICE, 'Caution Notice'),
    (SO_TYPE_LETTER_OF_ADVICE, 'Letter of Advice'),
    (SO_TYPE_REMEDIATION_NOTICE, 'Remediation Notice'),
)
HEAD_OFFICE_NAME=env('HEAD_OFFICE_NAME', 'KENSINGTON')
HTTP_HOST_FOR_TEST = env('HTTP_HOST_FOR_TEST', 'localhost:8123')

GROUP_CALL_EMAIL_TRIAGE = "call_email_triage"
GROUP_OFFICER = "officer"
GROUP_INSPECTION_OFFICER = "inspection_officer"
GROUP_MANAGER = "manager"
GROUP_VOLUNTEER = "volunteer"
GROUP_INFRINGEMENT_NOTICE_COORDINATOR = "infringement_notice_coordinator"
GROUP_PROSECUTION_COORDINATOR = "prosecution_coordinator"
GROUP_PROSECUTION_MANAGER = "prosecution_manager"
GROUP_PROSECUTION_COUNCIL = "prosecution_council"
GROUP_COMPLIANCE_MANAGEMENT_READ_ONLY = "compliance_management_read_only"
GROUP_COMPLIANCE_MANAGEMENT_CALL_EMAIL_READ_ONLY = "compliance_management_call_email_read_only"
GROUP_COMPLIANCE_MANAGEMENT_APPROVED_EXTERNAL_USER = "compliance_management_approved_external_user"
GROUP_COMPLIANCE_ADMIN = "compliance_admin"
GROUP_LICENSING_ADMIN = "licensing_admin"
GROUP_NAME_CHOICES = (
    (GROUP_CALL_EMAIL_TRIAGE, "Call Email Triage"),
    (GROUP_OFFICER, "Officer"),
    (GROUP_INSPECTION_OFFICER, "Inspection Officer"),
    (GROUP_MANAGER, "Manager"),
    (GROUP_VOLUNTEER, "Volunteer"),
    (GROUP_INFRINGEMENT_NOTICE_COORDINATOR, "Infringement Notice Coordinator"),
    (GROUP_PROSECUTION_COORDINATOR, "Prosecution Notice Coordinator"),
    (GROUP_PROSECUTION_MANAGER, "Prosecution Manager"),
    (GROUP_PROSECUTION_COUNCIL, "Prosecution Council"),
    (GROUP_COMPLIANCE_MANAGEMENT_READ_ONLY, "Compliance Management Read Only"),
    (GROUP_COMPLIANCE_MANAGEMENT_CALL_EMAIL_READ_ONLY, "Compliance Management Call Email Read Only"),
    (GROUP_COMPLIANCE_MANAGEMENT_APPROVED_EXTERNAL_USER, "Compliance Management Approved External User"),
    (GROUP_COMPLIANCE_ADMIN, "Compliance Admin"),
    (GROUP_LICENSING_ADMIN, "Licensing Admin"),
)

GROUP_WILDLIFE_COMPLIANCE_OFFICERS = "Wildlife Compliance Officers"
GROUP_WILDLIFE_COMPLIANCE_PAYMENT_OFFICERS = "Wildlife Compliance - Payment Officers"

AUTH_GROUP_COMPLIANCE_BUSINESS_ADMIN = 'Wildlife Compliance - Compliance Business Admin'
CUSTOM_AUTH_GROUPS = [
    AUTH_GROUP_COMPLIANCE_BUSINESS_ADMIN,
    ]
CALL_EMAIL_AVAILABLE_STATUS_VALUES = ['draft','open','closed']
VERSION_NO="1.0.1"

COMPLIANCE_LINKS_ENABLED = env('COMPLIANCE_LINKS_ENABLED', False)

MIDDLEWARE = MIDDLEWARE_CLASSES
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CSRF_TRUSTED_ORIGINS_STRING = decouple.config("CSRF_TRUSTED_ORIGINS", default='[]')
CSRF_TRUSTED_ORIGINS = json.loads(str(CSRF_TRUSTED_ORIGINS_STRING))

REPORTING_EMAIL = env('REPORTING_EMAIL', '').lower()

# This is needed so that the chmod is not called in django/core/files/storage.py
# (_save method of FileSystemStorage class)
# As it causes a permission exception when using azure network drives
FILE_UPLOAD_PERMISSIONS = None

RUNNING_DEVSERVER = len(sys.argv) > 1 and sys.argv[1] == "runserver"
EMAIL_INSTANCE = decouple.config("EMAIL_INSTANCE", default="DEV")

# Make sure this returns True when in local development
# so you can use the vite dev server with hot module reloading
DJANGO_VITE_DEV_MODE = RUNNING_DEVSERVER and EMAIL_INSTANCE == "DEV" and DEBUG is True  # DJANGO_VITE_DEV_MODE is preserved word.

logger.debug(f'DJANGO_VITE_DEV_MODE: {DJANGO_VITE_DEV_MODE}')

DJANGO_VITE = {
    "default": {
        "dev_mode": DJANGO_VITE_DEV_MODE,  # Indicates whether to serve assets via the ViteJS development server or from compiled production assets.
        "dev_server_host": "localhost", # Default host for vite (can change if needed)
        "dev_server_port": 9052, # Must match the dev server port (Ref: vite.config.js)
        "static_url_prefix": "/static/wildlifecompliance_vue" if DJANGO_VITE_DEV_MODE else "wildlifecompliance_vue/",  # The directory prefix for static files built by ViteJS.
    },
}
VUE3_ENTRY_SCRIPT = decouple.config(  # This is not a reserved keyword.
    "VUE3_ENTRY_SCRIPT",
    default="src/main.js",  # This path will be auto prefixed with the static_url_prefix from DJANGO_VITE above
)  # Path of the vue3 entry point script served by vite