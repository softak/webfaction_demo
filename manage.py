#!/usr/bin/env python
import os
import sys

# Edit this if necessary or override the variable in your environment.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings_local')

try:
    # For local development in a virtualenv:
    from funfactory import manage
except ImportError:
    # Production:
    # Add a temporary path so that we can import the funfactory
    tmp_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'vendor', 'src', 'funfactory')
    sys.path.append(tmp_path)

    from funfactory import manage

    # Let the path magic happen in setup_environ() !
    sys.path.remove(tmp_path)

if 'harvest' in sys.argv:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_test'
    import datetime_stub
    import paypal_stub
    datetime_stub.patch_step1()
    paypal_stub.patch()

manage.setup_environ(__file__, more_pythonic=False) # False as we don't use new Playdoh pattern

if __name__ == "__main__":
    manage.main()
