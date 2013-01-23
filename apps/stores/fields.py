from django.db import models
from django.contrib.gis.forms import GeometryField
from django.forms.fields import IntegerField
from django.core.exceptions import ImproperlyConfigured

from stores.widgets import LocationWidget, ZoomWidget
from stores.validators import validate_hex_color 

class LocationField(GeometryField):
    widget = LocationWidget

    def __init__(self, *args, **kwargs):
        self.default_error_messages['no_geom'] = 'This field is required.'
        super(LocationField, self).__init__(*args, **kwargs)


class ZoomField(IntegerField):
    widget = ZoomWidget

    def __init__(self, related_map_id=None, *args, **kwargs):
        if related_map_id is None:
            raise ImproperlyConfigured('Related map name for ZoomField not specified!')
        else:
            super(ZoomField, self).__init__(*args, **kwargs)
            self.widget.related_map_id = related_map_id


class ColorField(models.CharField):

    def __init__(self, *args, **kwargs):
        if not kwargs.has_key('max_length'):
            kwargs['max_length'] = 7
        if not kwargs.has_key('validators'):
            kwargs['validators'] = [validate_hex_color]
        super(ColorField, self).__init__(*args, **kwargs)

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^stores\.fields\.ColorField"])
