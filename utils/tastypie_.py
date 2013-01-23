from collections import Iterable

from django.forms.models import ModelChoiceField

from tastypie.authorization import DjangoAuthorization as DjangoAuthorization_
from tastypie.resources import ModelResource as ModelResource_
from tastypie.validation import FormValidation
from tastypie.exceptions import ImmediateHttpResponse
from tastypie.http import HttpBadRequest

from utils import to_json

class ModelResource(ModelResource_):

    def dispatch(self, request_type, request, **kwargs):
        request.POST # this is a fix! :)
        return super(ModelResource, self).dispatch(request_type, request, **kwargs)

    def deserialize(self, request, data, format='application/json'):
        if request.method == 'POST' or request.method == 'PUT':
            if format.startswith('application/x-www-form-urlencoded'):
                deserialized = getattr(request, request.method)
                data = {}
                for k, v in deserialized.lists():
                    data[k] = v[0] if len(v) == 1 else v
                return data
            elif format.startswith('multipart/form-data'):
                deserialized = getattr(request, request.method).copy()
                deserialized.update(request.FILES)
                return deserialized

        deserialized = super(ModelResource, self).deserialize(request, data, format=format)
        return deserialized

    def to_dict(self, obj=None, request=None):
        if isinstance(obj, Iterable):
            to_be_serialized = [self.full_dehydrate(
                self.build_bundle(obj=o, request=request)) for o in obj]
        else:
            to_be_serialized = self.full_dehydrate(
                self.build_bundle(obj=obj, request=request))
        return self._meta.serializer.to_simple(to_be_serialized, None)

    def to_json(self, obj=None, request=None):
        return to_json(self.to_dict(obj=obj, request=request))

    def raise_bad_request_error(self, request, response_dict):
        response = self.create_response(request, response_dict, response_class=HttpBadRequest)
        raise ImmediateHttpResponse(response=response)        
    

class ModelFormValidation(FormValidation):
    """
    Override tastypie's standard ``FormValidation`` since this does not care
    about URI to PK conversion for ``ToOneField`` or ``ToManyField``.
    """
    
    @staticmethod
    def uri_to_pk(uri):
        """
        Returns the integer PK part of a URI.

        Assumes ``/api/v1/resource/123/`` format. If conversion fails, this just
        returns the URI unmodified.

        Also handles lists of URIs
        """
        
        if uri is None:
            return None

        if isinstance(uri, int):
            return uri

        # convert everything to lists
        multiple = not isinstance(uri, basestring)
        uris = uri if multiple else [uri]

        # handle all passed URIs
        converted = []
        for one_uri in uris:
            try:
                # hopefully /api/v1/<resource_name>/<pk>/
                converted.append(int(one_uri.split('/')[-2]))
            except (IndexError, ValueError):
                return uri
                #raise ValueError(
                #    "URI %s could not be converted to PK integer." % one_uri)

        # convert back to original format
        return converted if multiple else converted[0]

    @staticmethod
    def convert_uris_to_pk(data, form_class):
        data = data.copy()

        relation_fields = [name for name, field in
                           form_class.base_fields.items()
                           if issubclass(field.__class__, ModelChoiceField)]

        for field in relation_fields:
            if field in data:
                data[field] = ModelFormValidation.uri_to_pk(data[field])
        return data

    def is_valid(self, bundle, request=None):
        data = bundle.data
        # Ensure we get a bound Form, regardless of the state of the bundle.
        if data is None:
            data = {}
        # copy data, so we don't modify the bundle
        data = data.copy()

        # convert URIs to PK integers for all relation fields
        relation_fields = [name for name, field in
                           self.form_class.base_fields.items()
                           if issubclass(field.__class__, ModelChoiceField)]
        for field in relation_fields:
            if field in data:
                data[field] = ModelFormValidation.uri_to_pk(data[field])

        # validate and return messages on error
        if request.method == 'PUT' and 'id' in bundle.data:
            # if we are updating a field, the model instance must also be
            # included in the arguments.
            instance = bundle.obj.__class__.objects.get(pk=bundle.data['id'])
            form = self.form_class(data, instance=instance)
        else:
            form = self.form_class(data)

        if form.is_valid():
            return {}
        return form.errors


from tastypie.bundle import Bundle
from tastypie.exceptions import ApiFieldError
from tastypie import fields

class CustomToManyField(fields.ToManyField):
    def dehydrate_related(self, bundle, related_resource):
        if not self.full:
            return related_resource.get_resource_uri(bundle)
        else:
            bundle_related = related_resource.build_bundle(obj=related_resource.instance, request=bundle.request)
            bundle_related.parent_obj = bundle.parent_obj
            return related_resource.full_dehydrate(bundle_related)
    
    def dehydrate(self, bundle):
        if not bundle.obj or not bundle.obj.pk:
            if not self.null:
                raise ApiFieldError("The model '%r' does not have a primary key and can not be used in a ToMany context." % bundle.obj)

            return []

        the_m2ms = None

        if isinstance(self.attribute, basestring):
            the_m2ms = getattr(bundle.obj, self.attribute)
        elif callable(self.attribute):
            the_m2ms = self.attribute(bundle)

        if not the_m2ms:
            if not self.null:
                raise ApiFieldError("The model '%r' has an empty attribute '%s' and doesn't allow a null value." % (bundle.obj, self.attribute))

            return []

        self.m2m_resources = []
        m2m_dehydrated = []

        for m2m in the_m2ms.all():
            m2m_resource = self.get_related_resource(m2m)
            m2m_bundle = Bundle(obj=m2m, request=bundle.request)
            m2m_bundle.parent_obj = bundle.obj # the point of CustomToManyField and the only difference from ToManyField
            self.m2m_resources.append(m2m_resource)
            m2m_dehydrated.append(self.dehydrate_related(m2m_bundle, m2m_resource))

        return m2m_dehydrated


class CustomToOneField(fields.ToManyField):
    def dehydrate_related(self, bundle, related_resource):
        if not self.full:
            return related_resource.get_resource_uri(bundle)
        else:
            bundle_related = related_resource.build_bundle(obj=related_resource.instance, request=bundle.request)
            bundle_related.parent_obj = bundle.parent_obj
            return related_resource.full_dehydrate(bundle_related)

    def dehydrate(self, bundle):
        attrs = self.attribute.split('__')
        foreign_obj = bundle.obj

        for attr in attrs:
            previous_obj = foreign_obj
            try:
                foreign_obj = getattr(foreign_obj, attr, None)
            except ObjectDoesNotExist:
                foreign_obj = None

            if not foreign_obj:
                if not self.null:
                    raise ApiFieldError("The model '%r' has an empty attribute '%s' and doesn't allow a null value." % (previous_obj, attr))

                return None

        self.fk_resource = self.get_related_resource(foreign_obj)
        fk_bundle = Bundle(obj=foreign_obj, request=bundle.request)
        fk_bundle.parent_obj = bundle.obj # the point of CustomToManyField and the only difference from ToOneField
        return self.dehydrate_related(fk_bundle, self.fk_resource)
