import decimal

from django.core.serializers import json
from django.db import models
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template.loader import render_to_string as render_to_string_
from django.utils import simplejson
from django.utils.decorators import method_decorator

from thumbnail import thumbnail
from utils.multi_file_field import MultiFileInput, MultipleFileField, MultipleImageField

def round_money(money):
    return decimal.Decimal(money).quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_UP)


def to_json(data):
    return simplejson.dumps(data, cls=json.DjangoJSONEncoder, sort_keys=True)

def from_json(data):
    return simplejson.loads(data)

class LoginRequiredMixin(object): # must go first
    @method_decorator(login_required)
    @method_decorator(csrf_protect)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


def render_to_json(context):
    return HttpResponse(simplejson.dumps(context, use_decimal=True), mimetype='application/json')


def render_to_string(request, template_name, context):
    return render_to_string_(template_name, context, context_instance=RequestContext(request))


def model_to_dict(instance, fields=None, exclude=None):
    opts = instance._meta
    data = {}
    for f in opts.fields:
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        else:
            data[f.name] = f.value_from_object(instance)
    return data


class QuerySetManager(models.Manager):

    use_for_related_fields = True

    def __init__(self, qs_class=models.query.QuerySet):
        self.queryset_class = qs_class
        super(QuerySetManager, self).__init__()

    def get_query_set(self):
        return self.queryset_class(self.model)

    def __getattr__(self, attr, *args):
        try:
            return getattr(self.__class__, attr, *args)
        except AttributeError:
            return getattr(self.get_query_set(), attr, *args)
