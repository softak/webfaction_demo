import commonware
from django import forms
from django.db.models import Q
from django.utils.translation import ugettext as _
from stores.fields import LocationField
from stores.models import Category, Store, Item, ItemImage,\
                          Discount, DiscountGroup, StoreDesign
from stores.widgets import AddressAutocompleteWidget
from utils import MultipleImageField
from utils.widgets import BootstrapClearableFileInput


log = commonware.log.getLogger('sd')


class ItemSearchForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(),
            empty_label=_('All Categories'),
            required=False)
    query = forms.CharField(required=False,
            widget=forms.TextInput(attrs={
                'class': 'search-query',
                'placeholder': _('Search for items'),
                }))

    def search(self, queryset=Item.objects.in_stock()):
        category = self.cleaned_data['category']
        query = self.cleaned_data['query']
        if category:
            queryset = queryset.filter(category=category)
        queryset = queryset.filter(Q(name__icontains=query) |
                                   Q(description__icontains=query))
        return queryset



class StoreCreationForm(forms.ModelForm):
    location = LocationField()

    class Meta:
        model   = Store
        fields  = ('name', 'category', 'phone', 'address', 'location')
        widgets = {'address':AddressAutocompleteWidget}


class StoreImageUploadForm(forms.ModelForm):
    window_image = forms.FileField(label=_('Store front image'),
                                   required=False,
                                   widget=BootstrapClearableFileInput)

    class Meta:
        model = Store
        fields = ('window_image',)

    # TODO validate: check file type


class ItemCreationForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(ItemCreationForm, self).__init__(*args, **kwargs)
        for name in ['price', 'quantity']:
            self.fields[name].widget.attrs.update({ 'autocomplete': 'off' })

    class Meta:
        exclude = ('store', 'discount_group')
        model = Item


class ItemImageCreationForm(forms.ModelForm):
    images = MultipleImageField(label=_('Upload new images'))

    class Meta:
        model = ItemImage
        exclude = ('image',)

    def save(self, commit=True):
        data = {}
        for field in self.instance._meta.fields:
            data[field.name] = getattr(self.instance, field.name)

        item_images = []
        for image in self.cleaned_data.get('images'):
            item_image = self._meta.model.objects.create(**data)
            item_image.image = image
            item_image.save()
            item_images.append(item_image)

        return item_images


class DiscountCreationForm(forms.ModelForm):

    class Meta:
        model = Discount


class DiscountGroupCreationForm(forms.ModelForm):

    class Meta:
        model = DiscountGroup


class ContactInformationForm(forms.ModelForm):
    country = forms.ChoiceField([('AU', 'Australia'), ('', '')])
    address = forms.CharField(widget=forms.Textarea)

    class Meta:
        model = Store
        fields = ('address', 'phone')

class StoreDesignForm(forms.ModelForm):

    class Meta:
        model   = StoreDesign
        exclude = ('store',)
