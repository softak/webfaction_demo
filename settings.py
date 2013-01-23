from funfactory.settings_base import *
from funfactory.manage import path


LESS_PREPROCESS = True
LESS_BIN = '/usr/local/bin/lessc'

COFFEE_PREPROCESS = True
COFFEE_BIN = 'coffee'

MEDIA_ROOT = path('m')

STATIC_ROOT = path('s')
STATIC_URL = '/static/'

STATICFILES_DIRS = (
    path('static'),
)

# For integration with staticfiles, this should be the same as STATIC_URL
# followed by 'admin/'.
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

# Bundles is a dictionary of two dictionaries, css and js, which list css files
# and js files that can be bundled together by the minify app.
MINIFY_BUNDLES = {

    'css': {

        'common': (
            'css/location-picker.css',
            'less/datetimepicker.less',

            'css/annotation.css',

            'less/bootstrap/bootstrap.less',
            'less/bootstrap-extension.less',
            'less/common.less',
            'less/layout.less',
            'less/home.less',

            'less/store.less',
            'less/view-item.less',

            'less/accounts.less',
            'less/profiles.less',
            'less/friends.less',
            'less/messages.less',
            'less/cart.less',
        ),

        'manage_store': (
            'less/manage-store.less',
            'less/autocomplite.less'
        ),
        'example_mobile_css': (
            'css/examples/mobile.css',
        ),
        'colorpicker_css':(
            'css/colorpicker.css',
        )
    },

    'js': {
        'modernizr': ('js/libs/modernizr-2.5.2.js',),
        'jquery': ('js/libs/jquery-1.7.1.js',),
        'public': (
            'js/libs/underscore-1.3.1.js',
            'js/libs/backbone-0.5.3.js',
            'js/libs/backbone-relational-0.4.0.js',
            'js/libs/backbone-tastypie-0.1.js',

            'js/libs/moment-1.4.0.js',
            'js/libs/accounting-0.3.2.js',

            'js/accounting.jquery.js',
            'js/location-picker.js',

            'js/libs/jquery.mousewheel.js',

            'js/libs/bootstrap-transition.js',
            'js/libs/bootstrap-alert.js',
            'js/libs/bootstrap-dropdown.js',
            'js/libs/bootstrap-scrollspy.js',
            'js/libs/bootstrap-tab.js',
            'js/libs/bootstrap-tooltip.js',
            'js/libs/bootstrap-popover.js',
            'js/libs/bootstrap-button.js',
            'js/libs/bootstrap-collapse.js',
            'js/libs/bootstrap-carousel.js',
            'js/libs/bootstrap-typeahead.js',
            'js/libs/bootstrap-modal-custom-old.js',

            'js/libs/jquery.timePicker.js',
            'js/libs/bootstrap-datepicker-custom.js',
            'coffee/datetimepicker.coffee',

            'js/utils.js',

            'js/backbone/base.js',
            'js/backbone/views.js',
            'js/backbone/collections.js',
            'coffee/backbone/models.coffee',

            'js/pages/models.js',
            'js/pages/views.js',
            'js/pages/routers.js',

            'js/stores/models.js',
            'js/stores/views.js',
            'coffee/stores/views.coffee',
            'js/stores/routers.js',

            'coffee/cart/models.coffee',
            'coffee/cart/views.coffee',
            'coffee/cart/routers.coffee',

            # 'js/libs/jquery-ui-1.8.17.js', Alexei, it breaks (overrides) $.datepicker from bootstrap-datepicker-custom.js!
            'js/libs/jquery.annotate.js',

            'js/init.js', # must go last
            'js/example.coffee',
        ),

        'manage': (
            'js/libs/fileuploader.js',
            'js/libs/ajax-file-form.js',

            'js/stores/manage-views.js',
            'js/stores/manage-routers.js',
            'coffee/stores/models.coffee',
            'coffee/stores/manage-views.coffee',
            'coffee/stores/manage-routers.coffee',
        ),

        'geo' : (
            'js/libs/geo.js',
        ),

        'jqueryui' : (
            'js/libs/jquery-ui-1.8.17.custom.min.js',
        ),

        'colorpicker_js' : (
            'js/colorpicker_init.js',
            'js/libs/colorpicker.js',
        ),
    }
}

# Defines the views served for root URLs.
ROOT_URLCONF = 'urls'

TEMPLATE_LOADERS = (
    'utils.jinja2_for_django.Loader', # must go first
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader'
)


# https://github.com/mozilla/funfactory/blob/master/funfactory/middleware.py
# bug with DELETE HTTP request
MIDDLEWARE_CLASSES = list(MIDDLEWARE_CLASSES)
MIDDLEWARE_CLASSES.pop(0) # FIXME
MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + [
    'cart.middleware.TryCompletePendingTransactionMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
]


TEMPLATE_CONTEXT_PROCESSORS += (
    'django.core.context_processors.static',
    'stores.context_processors.has_store',
    'accounts.context_processors.auth_forms',
    'django_messages.context_processors.inbox',
    'friends.context_processors.friendship_requests_counter',
    'utils.context_processors.settings',
)


INSTALLED_APPS = list(INSTALLED_APPS) + [
    'django.contrib.sites',
    'django.contrib.flatpages',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.staticfiles',
    'django.contrib.gis',
    'django_extensions',

    'lettuce.django',
    'utils',
    'pages',
    'accounts',
    'profiles',
    'friends',
    'stores',
    'cart',
    'messages',

    'djkombu',
    'sorl.thumbnail',
    'django_messages',
    'facebook',
    'south', # must go last
]


AUTH_PROFILE_MODULE = 'profiles.Profile'


AUTHENTICATION_BACKENDS = [
    'accounts.backends.EmailOrUsernameModelBackend', # must go first
    'facebook.backend.FacebookBackend',
]

# Tells the extract script what files to look for L10n in and what function
# handles the extraction. The Tower library expects this.

# # Use this if you have localizable HTML files:
# DOMAIN_METHODS['lhtml'] = [
#    ('**/templates/**.lhtml',
#        'tower.management.commands.extract.extract_tower_template'),
# ]

# # Use this if you have localizable HTML files:
# DOMAIN_METHODS['javascript'] = [
#    # Make sure that this won't pull in strings from external libraries you
#    # may use.
#    ('media/js/**.js', 'javascript'),
# ]

LOGGING = dict(loggers=dict(playdoh = {'level': logging.DEBUG}))

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# Minimum time interval between confirmation-like emails resends (in minutes)
CONFIRMATION_RESEND_TIMEOUT = 5

# django_facebook_oauth settings
FACEBOOK_APP_ID = ''
FACEBOOK_APP_SECRET = ''
FACEBOOK_SCOPE = 'email,user_birthday'
FACEBOOK_FORCE_VERIFICATION = True

PP_API_ENVIRONMENT = 'sandbox'
PP_API_EMAIL = 'sllr1_1319977604_biz@gmail.com'
PP_API_USERID = 'sllr1_1319977604_biz_api1.gmail.com'
PP_API_PASSWORD = '1319977630'
PP_API_SIGNATURE = 'AIIafItLgz5fj4SuyH4SPcjKJp-pAyNi8Piqc-yfBieFP7FY0X0WF.z5'
PP_API_APPLICATION_ID = 'APP-80W284485P519543T' # common ID for sandbox applications

# for development purporses
# ./manage.py createcachetable cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'cache',
    }
}

import djcelery
djcelery.setup_loader()

BROKER_BACKEND = 'djkombu.transport.DatabaseTransport'
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'

# Use these settings with RabbitMQ:
# BROKER_HOST = 'localhost'
# BROKER_PORT = 5672
# BROKER_USER = ''
# BROKER_PASSWORD = ''
# BROKER_VHOST = '/'

CELERY_ALWAYS_EAGER = False
CELERY_IGNORE_RESULT = True
CELERY_RESULT_BACKEND = 'amqp'
CELERY_IMPORTS = ('cart.tasks',)


EMAIL_RESEND_INTERVAL = 5

import decimal
SD_FEE = decimal.Decimal(95) / decimal.Decimal(100)

from datetime import timedelta
SHIPPING_PRICE_REQUEST_PROCESSING_PERIOD = timedelta(hours=1)
SHIPPING_PAY_PERIOD = timedelta(hours=10)
