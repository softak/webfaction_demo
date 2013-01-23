from django.conf import settings
from django.conf.urls.defaults import *
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.simple import direct_to_template

from django.contrib import admin
from funfactory.admin import site as admin_site
admin.site = admin_site
admin.autodiscover()

urlpatterns = patterns('',
    (r'', include('pages.urls')),
    (r'', include('accounts.urls')),
    (r'', include('profiles.urls')),
    (r'^stores/', include('stores.urls')),
    (r'^friendship/', include('friends.urls')),
    (r'^messages/', include('messages.urls')),
    (r'^cart/', include('cart.urls')),

    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/', include(admin.site.urls)),

    # TODO page ;)
    url(r'^TODO/$', direct_to_template, {
            'template': 'TODO.j.html'},
        name='TODO'),
)

urlpatterns+= patterns('django.contrib.flatpages.views',
    url(r'^pages/address-formats/$', 'flatpage', { 'url': '/pages/address-formats/' }, name='pages.address-formats'),
)

## In DEBUG mode, serve static and media files through Django.
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.lstrip('/').rstrip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
