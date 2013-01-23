from django.conf.urls.defaults import *
from django.views.generic import TemplateView
from tastypie.api import Api
from cart.resources import SocialCartResource, PersonalCartResource
from cart import views


v1_api = Api(api_name='v1')
v1_api.register(SocialCartResource())
v1_api.register(PersonalCartResource())

urlpatterns = patterns('',
    (r'^api/', include(v1_api.urls)),

    url(r'^social_mockup/$', TemplateView.as_view(template_name='cart/social_mockup.j.html')),

    url(r'^personal/$', views.personal_cart, name='cart.personal_cart'),
    url(r'^social/$', views.social_cart, name='cart.social_cart'),

    url(r'^preview_social_cart/$', views.preview_social_cart, name='cart.preview_social_cart'),
    url(r'^preview_personal_cart/$', views.preview_personal_cart, name='cart.preview_personal_cart'),

    url(r'^approve_social_cart/$', views.approve_cart, { 'cart': 'social' }, name='cart.approve_social_cart'),
    url(r'^approve_personal_cart/$', views.approve_cart, { 'cart': 'personal' }, name='cart.approve_personal_cart'),

    url(r'^cancel_pending_transaction/$', views.cancel_pending_transaction, name='cart.cancel_pending_transaction'),

    #url(r'^approved/$', views.approved_tags, name='cart.approved_tags'),
)
