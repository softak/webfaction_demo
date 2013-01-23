from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic import TemplateView


urlpatterns = patterns('pages.views',
    url(r'^$', 'home', name='pages.home'),

    url(r'^rrp/$', 'request_refund_permission', name='pages.rrp'),
    url(r'^rrp_callback/$', 'request_refund_permission_callback', name='pages.rrp_callback'),
    url(r'^mpp/$', 'make_parallel_payment', name='pages.mpp'),
    url(r'^mpp_callback/$', 'make_parallel_payment_callback', name='pages.mpp_callback'),

    url(r'^new_home/$', 'new_home')
)
