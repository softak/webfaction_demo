import commonware
import json
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import DetailView
from django.views.generic.edit import UpdateView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.shortcuts import render
from utils import LoginRequiredMixin
from profiles.models import Profile
from profiles.forms import ProfileEditForm, GeoLocationPointForm,\
                           FacebookNotificationOptionsForm

log = commonware.log.getLogger('sd')


class ProfileView(LoginRequiredMixin, DetailView):
    model = User
    context_object_name = 'requested_user'
    template_name = 'profiles/profile.j.html'

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        user = self.object
        context['profile'] = user.get_profile()
        return context

    def get_object(self, *args, **kwargs):
        if not self.kwargs.has_key('pk'):
            return self.request.user
        else:
            return super(ProfileView, self).get_object(*args, **kwargs)


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = Profile
    template_name = 'profiles/edit.j.html'

    def get_object(self, queryset=None):
        return self.request.user.get_profile()

    def get_initial(self):
        user = self.request.user
        return { 'first_name': user.first_name,
                 'last_name': user.last_name }

    def get_form_class(self):
        return ProfileEditForm

    def form_valid(self, form):
        user = self.request.user
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.save()
        return super(ProfileEditView, self).form_valid(form)

    def get_success_url(self):
        return self.request.user.get_profile().get_absolute_url()


def set_geolocation(request):
    form = GeoLocationPointForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest(json.dumps(form.errors))
    request.session['geolocation'] = Point(form.getLat(), form.getLng())
    return HttpResponse()


@login_required
def facebook_connect(request):
    form = FacebookNotificationOptionsForm()
    return render(request, "profiles/facebook_connect.j.html", {
        'form': form
    })
