# This module should be in the root folder of project.
# We can't put it in the `utils` module, as `patch_step1` function
# called before any django modules loaded.

import sys
import datetime as datetime_orig
from datetime import datetime as datetime_datetime_orig
from datetime import date as datetime_date_orig


class DatetimeStub(object):

    class datetime(datetime_datetime_orig):
        @classmethod
        def get_delay(cls):
            return datetime_orig.timedelta(0)
        
        @classmethod
        def set_delay(cls, delay):
            cls.get_delay = classmethod(
                    lambda _: datetime_orig.timedelta(**delay))
        
        @classmethod
        def utcnow(cls):
            return datetime_datetime_orig.utcnow() + cls.get_delay()
        
        @classmethod
        def now(cls):
            return datetime_orig.datetime.now() + cls.get_delay()

    class date(datetime_date_orig):
        def __new__(cls, *args, **kwargs):
            return datetime_date_orig.__new__(
                    datetime_date_orig, *args, **kwargs)

    def __getattr__(self, attr):
        return getattr(datetime_orig, attr)


def patch_step1():
    # Should be called before django modules loaded, say in the ./manage.py
    sys.modules['datetime'] = DatetimeStub()


def patch_step2():
    # Should be called before tests.
    from django.db.models.fields import DateField
    old_to_python = DateField.to_python
    DateField.to_python = lambda self, value: old_to_python(self, str(value))
