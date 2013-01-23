from lettuce import before, after, world
from splinter.browser import Browser
from django.test.utils import setup_test_environment, teardown_test_environment
from django.test.client import Client
from django.core.management import call_command
from django.db import connection
from django.conf import settings

import datetime_stub


@before.all
def initial_setup():
    datetime_stub.patch_step2()

@before.harvest
def initial_setup(server):
    """Monkey patch, but it saves migration history from being flushed"""
    from django.db import connection
    old_django_table_names = connection.introspection.django_table_names
    def new_django_table_names(*args, **kwargs):
        table_names = old_django_table_names(*args, **kwargs)
        table_names.remove('south_migrationhistory')
        return table_names
    
    call_command('syncdb', interactive=False, verbosity=0)
    call_command('migrate', interactive=False, verbosity=0)
    
    connection.introspection.django_table_names = new_django_table_names
    
    world.client = Client()

@before.each_feature
def reset_data(scenario):
    call_command('flush', interactive=False, verbosity=0)
