from django.contrib import admin
from django import forms

from stores.models import Category, Store, \
                          Item, ItemImage, StoreDesign, \
                          Discount, DiscountGroup
from stores.fields import LocationField, ZoomField


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

class StoreAdminForm(forms.ModelForm):
    location = LocationField()

    class Meta:
        model = Store

class ModeratedStoreAdminForm(forms.ModelForm):
    location = LocationField()

    class Meta:
        model = Store

class StoreAdmin(admin.ModelAdmin):
    form = StoreAdminForm

    def get_moderated_object_form(self, model_class):
        return ModeratedStoreAdminForm

class ItemAdmin(admin.ModelAdmin):
    pass

class ItemImageAdmin(admin.ModelAdmin):
    pass

class DiscountAdmin(admin.ModelAdmin):
    pass

class DiscountGroupAdmin(admin.ModelAdmin):
    pass

class StoreDesignAdmin(admin.ModelAdmin):
    list_display = ['store', 'is_repeated', 'background_color']

    class Media:
        css = {
            'all' : ('css/colorpicker.css',),
        }
        js = ('js/libs/jquery-1.7.1.js', 
              'js/libs/colorpicker.js', 
              'js/colorpicker_init.js')

admin.site.register(Category, CategoryAdmin)
admin.site.register(Store, StoreAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(ItemImage, ItemImageAdmin)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(DiscountGroup, DiscountGroupAdmin)
admin.site.register(StoreDesign,StoreDesignAdmin)
