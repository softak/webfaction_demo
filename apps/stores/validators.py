import re
from django.core.exceptions import ValidationError

def validate_hex_color(val):
    if not re.match('#[0-9a-fA-F]{6}', val):
        raise ValidationError(u'%s is not a hex color' % val)
