import uuid
import datetime

from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

from django_messages.models import Message
from django_messages.fields import CommaSeparatedUserField
from django_messages.utils import format_quote


class MessageForm(forms.ModelForm):
    subject = forms.CharField(label=_('Subject'))
    body = forms.CharField(label=_('Body'), widget=forms.Textarea())

    def __init__(self, sender, *args, **kw):
        kw.pop('recipient_filter', None)
        self.sender = sender
        super(MessageForm, self).__init__(*args, **kw)

    class Meta:
        model = Message
        fields = ('recipient', 'subject', 'body',)

    def create_recipient_message(self, recipient, message):
        return Message(
            owner=recipient,
            sender=self.sender,
            to=recipient.username,
            recipient=recipient,
            subject=message.subject,
            body=message.body,
            thread=message.thread,
            sent_at=message.sent_at)

    def get_thread(self, message):
        return message.thread or uuid.uuid4().hex

    def save(self, commit=True):
        recipient = self.cleaned_data['recipient']
        instance = super(MessageForm, self).save(commit=False)
        instance.sender = self.sender
        instance.owner = self.sender
        instance.recipient = recipient
        instance.thread = self.get_thread(instance)
        instance.unread = False
        instance.sent_at = datetime.datetime.now()

        msg = self.create_recipient_message(recipient, instance)

        if commit:
            instance.save()
            msg.save()
     
        return instance, [msg]


class ComposeForm(MessageForm):

    def __init__(self, *args, **kw):
        initial = kw.pop('initial', {})

        if initial.has_key('recipients'):
            initial['recipient'] = initial.pop('recipients')
        kw['initial'] = initial
            
        super(ComposeForm, self).__init__(*args, **kw)
        self.fields['recipient'].widget = forms.widgets.HiddenInput()

    class Meta:
        model = Message
        fields = ('recipient', 'subject', 'body',)
    

class ReplyForm(MessageForm):

    def __init__(self, sender, message, *args, **kw):
        self.parent_message = message

        initial = kw.pop('initial', {})
        initial['recipient'] = message.sender.id
        initial['body'] = self.quote_message(message)
        initial['subject'] = self.quote_subject(message.subject)
        kw['initial'] = initial

        super(ReplyForm, self).__init__(sender, *args, **kw)
        self.fields['recipient'].widget = forms.widgets.HiddenInput()
    
    class Meta:
        model = Message
        fields = ('recipient', 'subject', 'body',)

    def quote_message(self, original_message):
        return format_quote(original_message.sender, original_message.body)

    def quote_subject(self, subject):
        return u'Re: %s' % subject

    def create_recipient_message(self, recipient, message):
        msg = super(ReplyForm, self).create_recipient_message(recipient, message)
        msg.replied_at = datetime.datetime.now()

        try:
            msg.parent_msg = Message.objects.get(
                owner=recipient,
                sender=message.recipient,
                recipient=message.sender,
                thread=message.thread)
        except (Message.DoesNotExist, Message.MultipleObjectsReturned):
            pass

        return msg

    def get_thread(self, message):
        return self.parent_message.thread

    def save(self, commit=True):
        instance, message_list = super(ReplyForm, self).save(commit=False)
        instance.replied_at = datetime.datetime.now()
        instance.parent_msg = self.parent_message
        if commit:
            instance.save()
            for msg in message_list:
                msg.save()

        return instance, message_list
