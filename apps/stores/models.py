import math
import decimal
from django.contrib.gis.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.db.models import Q
from django.db.models.query import QuerySet
from utils import QuerySetManager
from stores.fields import ColorField


class Category(models.Model):
    name = models.CharField(_('name'),
        max_length=50)
    icon = models.ImageField(_('icon'),
        upload_to='category-icons',
        null=True)
    marker = models.ImageField(_('marker'),
        upload_to='category-markers',
        null=True)

    class Meta:
       verbose_name_plural = "categories"

    def __unicode__(self):
        return self.name


class Store(models.Model):
    user = models.OneToOneField(User,
        related_name='store')
    name = models.CharField(_('business name'),
        max_length=100)
    category = models.ForeignKey(Category,
        related_name='stores')
    location = models.PointField(_('location'),
        srid=4326)
    address = models.CharField(_('address'),
        max_length=1000)
    is_active = models.BooleanField(_('active'),
        default=False)
    window_image = models.ImageField(_('window image'),
        upload_to='store-images',
        null=True,
        blank=True)
    phone = models.CharField(_('phone'),
        max_length=50)
    paypal_email = models.EmailField(_('PayPal e-mail'),
        null=True,
        blank=True,
        max_length=100)

    objects = models.GeoManager()

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('stores.view_store', [str(self.id)])

    def get_buyer_ids(self):
        from cart.models import SocialTag, PersonalTag
        r1 = SocialTag.objects.filter(buy__store=self) \
                              .values_list('user__id', flat=True).distinct()
        r2 = PersonalTag.objects.filter(item__store=self) \
                                .values_list('user__id', flat=True).distinct()
        return list(r1) + list(r2)

    def get_buyers(self):
        return User.objects.filter(id__in=self.get_buyer_ids())


class StoreDesign(models.Model):
    store = models.OneToOneField(Store, 
        related_name='design')
    background_image = models.ImageField(_('Image'),
        upload_to='store_desings',
        null=True,
        blank=True)
    is_repeated = models.BooleanField(_('Repeat'), 
        default=False)
    background_color = ColorField(_('Color'), 
        default='#ffffff')


class ItemQuerySet(QuerySet):
    def in_stock(self):
        return self.exclude(is_out_of_stock=True) \
                   .filter(Q(quantity__gt=0) | Q(quantity__isnull=True))


class Item(models.Model):
    store = models.ForeignKey(Store,
        related_name='items')
    name = models.CharField(_('name'),
        max_length=100)
    description = models.CharField(_('description'),
        max_length=1000)
    price = models.DecimalField(_('price'),
        max_digits=10,
        decimal_places=2)
    discount = models.PositiveSmallIntegerField(_('advertised discount'),
        default=0)
    # TODO make NOT NULL
    quantity = models.PositiveIntegerField(_('quantity'),
        null=True,
        blank=True)
    is_out_of_stock = models.BooleanField(_('is out of stock'), 
        default=False)
    discount_group = models.ForeignKey('DiscountGroup',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='items')

    objects = QuerySetManager(qs_class=ItemQuerySet)

    def save(self, *args, **kwargs):
        if not self.discount_group is None:
            if self.store != self.discount_group.discount.store:
                raise ValidationError('Item can\'t belong to specified discount group!')
        return super(Item, self).save(*args, **kwargs)

    def get_default_image(self):
        default_images = self.images.filter(is_default=True)
        if default_images.exists():
            return default_images[0].image
        elif self.images.exists():
            return self.images.all()[0].image
        else:
            return None
    
    @models.permalink
    def get_absolute_url(self):
        return ('stores.item', [str(self.id)])

    def __unicode__(self):
        return self.name


class DiscountGroup(models.Model): # TODO add store field?
    name = models.CharField(_('discount name'),
        max_length=100)
    discount = models.ForeignKey('Discount',
        related_name='discount_groups')


class Discount(models.Model):
    store = models.ForeignKey(Store,
        related_name='discount_models')
    name = models.CharField(_('discount name'),
        max_length=100)
    for_additional_item = models.DecimalField(_('discount for each additional item'),
        max_digits=4,
        decimal_places=2)
    for_additional_buyer = models.DecimalField(_('discount for each additional buyer'),
        max_digits=4,
        decimal_places=2)
    lower_bound = models.DecimalField(_('lower bound'),
        max_digits=4,
        decimal_places=2)
    
    def __unicode__(self):
        return 'Discount: %s' % self.name

    def apply(self, items_number=None, buyers_number=None):
        discount = math.pow((100 - self.for_additional_buyer) / decimal.Decimal(100), buyers_number) * \
                   math.pow((100 - self.for_additional_item) / decimal.Decimal(100), items_number)
        return max(decimal.Decimal(discount), (100 - self.lower_bound) / decimal.Decimal(100))


class ItemImage(models.Model):
    item = models.ForeignKey(Item,
        related_name='images')
    image = models.ImageField(_('image'),
        upload_to='item-images')
    is_default = models.BooleanField(_('is default'),
        default=False)
    
    def __unicode__(self):
        return 'Image of %s' % self.item.name
