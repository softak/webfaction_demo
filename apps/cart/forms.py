from django import forms
from cart.models import PersonalTag, SocialTag, SocialBuy
from stores.models import Store


class PersonalTagForm(forms.ModelForm):

    def clean(self):
        try:
            self.instance = PersonalTag.objects.get( # TODO draft
                user=self.cleaned_data['user'],
                item=self.cleaned_data['item'])
        except PersonalTag.DoesNotExist:
            # TODO check if quantity > 0
            pass
        return self.cleaned_data

    def save(self, *args, **kwargs):
        if self.cleaned_data['quantity'] > 0:
            return super(PersonalTagForm, self).save(*args, **kwargs)
        else:
            return self.instance.delete()

    class Meta:
        model = PersonalTag


class SocialTagForm(forms.ModelForm):

    def clean(self):
        try:
            self.instance = SocialTag.objects.draft().get(
                user=self.cleaned_data['user'],
                buy=self.cleaned_data['buy'],
                item=self.cleaned_data['item'])
        except SocialTag.DoesNotExist:
            # TODO check if quantity > 0
            #if tag.item.store != tag.buy.store:
                ## check if buy belongs to the same store that item
                #response = self.create_response(bundle.request, 'TODO', response_class=HttpBadRequest)
                #raise ImmediateHttpResponse(response=response)
            #if not (tag.buy.is_active or tag.buy.user == bundle.request.user):
                ## check if the buy is active or owned by requested user
                #response = self.create_response(bundle.request, 'TODO', response_class=HttpBadRequest)
                #raise ImmediateHttpResponse(response=response)
            pass
        return self.cleaned_data

    def save(self, *args, **kwargs):
        if self.cleaned_data['quantity'] > 0:
            return super(SocialTagForm, self).save(*args, **kwargs)
        else:
            return self.instance.delete()

    class Meta:
        model = SocialTag


class SocialBuyForm(forms.ModelForm):
    id = forms.IntegerField(required=False)
    store = forms.ModelChoiceField(
        #TODO restrict choice to moderated stores
        queryset=Store.objects.all(), 
        required=False) 
    finish_date = forms.DateTimeField(required=False)

    def _post_clean(self):
        if not self.instance.id:
            super(SocialBuyForm, self)._post_clean()

    def clean(self):
        data = self.cleaned_data

        c1 = data.has_key('store') and data.has_key('finish_date') and\
             (not data['store'] is None and not data['finish_date'] is None)
        c2 = data.has_key('id') and\
             not data['id'] is None

        if c1 and c2:
            raise forms.ValidationError('err1')
        elif (not c1) and (not c2):
            raise forms.ValidationError('err2')

        if c1:
            pass
        elif c2:
            try:
                self.instance = SocialBuy.objects.get(id=data['id'])
            except SocialBuy.DoesNotExist:
                raise forms.ValidationError('err3')

        return self.cleaned_data

    class Meta:
        model = SocialBuy
