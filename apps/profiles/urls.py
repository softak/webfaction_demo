from django.conf.urls.defaults import *
from tastypie.api import Api
from profiles import views
from profiles.resources import UserResource

v1_api = Api(api_name='v1')
v1_api.register(UserResource())

urlpatterns = patterns('',
    (r'^api/', include(v1_api.urls)),

    url(r'^users/(?P<pk>\d+)/$', views.ProfileView.as_view(),
        name='profiles.profile'),
    url(r'^profile/$', views.ProfileView.as_view(),
        name='profiles.profile'),
    url(r'^profile/edit/$', views.ProfileEditView.as_view(),
        name='profiles.edit'),
    url(r'^profile/facebook/$', views.facebook_connect,
        name='profiles.facebook_connect'),
    url(r'^geo_location/$', views.set_geolocation,
        name='profiles.set_geolocation')
)
