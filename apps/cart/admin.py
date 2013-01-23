from django.contrib import admin
from cart.models import SocialTag, SocialBuy, PersonalTag,\
                        Transaction, ShippingRequest, PickupRequest


class SocialTagAdmin(admin.ModelAdmin):
    readonly_fields = ('item', 'user', 'quantity', 'buy',
                       'transaction', 'paid',)
admin.site.register(SocialTag, SocialTagAdmin)

admin.site.register(PersonalTag)
admin.site.register(SocialBuy)
admin.site.register(Transaction)
admin.site.register(ShippingRequest)
admin.site.register(PickupRequest)
