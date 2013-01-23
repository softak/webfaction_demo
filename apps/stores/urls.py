from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic import TemplateView
from stores import views

from tastypie.api import Api
from stores.resources import StoreResource, \
                             DiscountResource, DiscountGroupResource, \
                             ItemImageResource, ItemResource, DetailItemResource, \
                             PendingShippingRequestResource


v1_api = Api(api_name='v1')
v1_api.register(StoreResource())
v1_api.register(ItemResource())
v1_api.register(DiscountResource())
v1_api.register(DiscountGroupResource())
v1_api.register(ItemImageResource())
v1_api.register(DetailItemResource())
v1_api.register(PendingShippingRequestResource())


urlpatterns = patterns('',

    url(r'^(?P<store_id>\d+)/$', views.view_store,
        name='stores.view_store'),

    url(r'^items/(?P<pk>\d+)/$', views.ItemView.as_view(),
        name='stores.item'),

    url(r'^search/$', views.search, name='stores.search'),

    # Managing

    url(r'^manage/$', direct_to_template, {
            'template': 'stores/manage/home.j.html'},
        name='stores.manage'),
        
    url(r'^manage/design/$', views.ChangeStoreDesign.as_view(), 
        name='stores.design'),
    
    url(r'^manage/image/$', views.store_image,
        name='stores.store_image'),

    url(r'^manage/create/$', views.CreateStoreView.as_view(),
        name='stores.create_store'),

    url(r'^manage/create/done/$', views.CreateStoreDoneView.as_view(),
        name='stores.create_store_done'),

    url(r'^manage/items/$', views.ManageItemsView.as_view(),
        name='stores.manage_items'),

    url(r'^manage/discounts/$', views.ManageDiscountsView.as_view(),
        name='stores.manage_discounts'),

    url(r'^manage/discount_groups/$', views.ManageDiscountGroupsView.as_view(),
        name='stores.manage_discount_groups'),

    url(r'^manage/contact_information/$', views.ManageContactInformationView.as_view(),
        name='stores.manage_contact_information'),
    
    url(r'^manage/shipping/$', views.ManageShippingRequests.as_view(),
        name='stores.manage_shipping'),

    (r'^api/', include(v1_api.urls)),
)
