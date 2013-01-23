from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404

from django_messages.models import Message
from django_messages import views as django_messages_views

from messages.forms import ComposeForm, ReplyForm


def compose(request, *args, **kwargs):
    kwargs.update({
        'template_name': 'messages/compose.j.html',
        'form_class': ComposeForm,
        'extra_context': {
            'recipient': User.objects.get(id=int(kwargs.get('recipient')))
        }
    })
    return django_messages_views.compose(request, *args, **kwargs)


def reply(request, *args, **kwargs):
    message_id = int(kwargs.get('message_id'))
    message = get_object_or_404(Message, pk=message_id, owner=request.user)
    kwargs.update({
        'template_name': 'messages/compose.j.html',
        'form_class': ReplyForm,
        'extra_context': {
            'recipient': message.sender
        }
    })
    return django_messages_views.reply(request, *args, **kwargs)
