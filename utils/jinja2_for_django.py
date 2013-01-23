"""

    A Jinja2 template loader for Django 1.2+
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Add the following to your settings.py file.  (The comma is important!) 

        TEMPLATE_LOADERS = ('utils.jinja2_for_django.Loader',)

"""

from jingo import env
from django.template.loader import BaseLoader
from django.template.context import BaseContext
from django.template import TemplateDoesNotExist
import jinja2

class Template(jinja2.Template):
    def _flatten_context(self, context):
        # flatten the Django Context into a single dictionary.
        context_dict = {}
        for d in context.dicts:
            if isinstance(d, BaseContext):
                context_dict = self._flatten_context(d)
            else:
                context_dict.update(d)
        return context_dict

    def render(self, context):
        context_dict = self._flatten_context(context)
        return super(Template, self).render(**context_dict)


def get_env_globals():
    from friends.helpers import get_friends_of, are_friends, is_invited
    from stores.helpers import gen_backround
    from utils.thumbnail import thumbnail
    return locals()

from django.utils import simplejson

def get_env_filters():
    from django.template.defaultfilters import linebreaksbr, date, escapejs
    from sorl.thumbnail.templatetags.thumbnail import margin
    from markdown2 import markdown
    json_encode = lambda obj: simplejson.dumps(obj, use_decimal=True)
    return locals()


class Loader(BaseLoader):
    is_usable = True

    env = env
    env.template_class = Template

    env.globals.update(get_env_globals())
    env.filters.update(get_env_filters())

    def load_template(self, template_name, template_dirs=None):
        bits = template_name.split('.')
        if len(bits) > 1 and bits[-2] == 'j':
            try:
                template = self.env.get_template(template_name)
            except jinja2.TemplateNotFound:
                raise TemplateDoesNotExist(template_name)
            return template, template.filename
        raise TemplateDoesNotExist(template_name)
