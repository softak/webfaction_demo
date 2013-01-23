from django.conf.urls.defaults import *
from django.views.generic.simple import redirect_to
from django.views.decorators.csrf import csrf_protect

from django_messages import views as django_messages_views
from messages.views import compose, reply


urlpatterns = patterns('',

    url(r'^$', redirect_to, {'url': 'inbox/'}),

    url(r'^inbox/$', django_messages_views.inbox,
        { 'template_name': 'messages/inbox.j.html' }, name='messages.inbox'),

    url(r'^outbox/$', django_messages_views.outbox,
        { 'template_name': 'messages/outbox.j.html' }, name='messages.outbox'),

    url(r'^compose/(?P<recipient>[\+\w]+)/$', compose,
        name='messages.compose_to'),

    url(r'^reply/(?P<message_id>[\d]+)/$', reply,
        name='messages.reply'),

    url(r'^view/(?P<message_id>[\d]+)/$', django_messages_views.view,
        { 'template_name': 'messages/view.j.html' }, name='messages.detail'),

    url(r'^delete/(?P<message_id>[\d]+)/$', django_messages_views.delete,
        name='messages.delete')
)
