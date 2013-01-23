import commonware.log
from datetime import datetime, timedelta
import re
from session_csrf import anonymous_csrf
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.base import View, TemplateView
from django.views.generic import ListView, DetailView, FormView
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.core.urlresolvers import reverse
from django.http import Http404

from stores.resources import DiscountResource, DiscountGroupResource, \
                             ItemResource, ItemImageResource, DetailItemResource, \
                            PendingShippingRequestResource
from stores.models import Store, Item, ItemImage, Discount, DiscountGroup, \
                          StoreDesign
from stores.forms import StoreCreationForm, StoreImageUploadForm, \
                         ItemCreationForm, ItemImageCreationForm, \
                         DiscountCreationForm, DiscountGroupCreationForm, \
                         ContactInformationForm, \
                         ItemSearchForm, StoreDesignForm
from cart.models import PersonalTag, SocialBuy, SocialTag, ShippingRequest, paypalAP
from cart.forms import SocialBuyForm
from friends.models import Friendship

from utils import LoginRequiredMixin, render_to_string, thumbnail
log = commonware.log.getLogger('shoppindomain')


@login_required
def search(request):
    form = ItemSearchForm(request.GET)
    return render(request, 'stores/search.j.html', {
        'form': form
    })


# TODO store.get_buyers is slow.
# Maybe we should denormalize database and add to Store model m2m-field `buyers`
@login_required
@csrf_protect
def view_store(request, store_id=None):
    store = get_object_or_404(Store, pk=int(store_id))

    friend_ids = map(lambda friend: friend['id'],
            Friendship.objects.friends_of(request.user).values('id'))
    buyer_ids = store.get_buyer_ids()

    buyers = User.objects.filter(id__in=buyer_ids).exclude(id=request.user.id)

    return render(request, 'stores/store.j.html', { 
        'store': store,
        'friend_buyers': buyers.filter(id__in=friend_ids),
        'other_buyers': buyers.exclude(id__in=friend_ids),
    })


class CreateStoreView(LoginRequiredMixin, CreateView):
    model = Store
    template_name = 'stores/manage/create.j.html'

    def get_form_class(self):
        return StoreCreationForm

    def form_valid(self, form):
        store = form.save(commit=False)
        store.user = self.request.user
        store.save()
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse('stores.create_store_done')

    def dispatch(self, request, *args, **kwargs):
        if hasattr(request.user, 'store'):
            return render(request, self.template_name, {})
        else:
            return super(CreateStoreView, self).dispatch(request, *args, **kwargs)


@login_required
@csrf_protect
def store_image(request):
    if not hasattr(request.user, 'store'):
        raise Http404()

    store = request.user.store
    if request.method == 'POST':
        form = StoreImageUploadForm(request.POST,
                request.FILES,
                instance=store)
        if form.is_valid():
            form.save()
            return redirect(store_image)
    else:
        form = StoreImageUploadForm(instance=store)

    return render(request, 'stores/manage/image.j.html', {
        'image': request.user.store.window_image,
        'form': form
    })


class CreateStoreDoneView(LoginRequiredMixin, TemplateView):
    template_name = 'stores/manage/create_done.j.html'

    def get_context_data(self, **kwargs):
        request_token = self.request.GET.get('request_token', None)
        verification_code = self.request.GET.get('verification_code', None)
        store = self.request.user.store
        
        if store.paypal_email and not store.is_active:
            return {}

        if (not request_token is None) and (not verification_code is None):
            response = paypalAP.callPermissions('GetAccessToken',
                token=request_token,
                verifier=verification_code)

            response = paypalAP.callPermissionsOnBehalf('GetBasicPersonalData',
                    access_token = response.token,
                    secret_token = response.tokenSecret,
                    **{
                        'attributeList.attribute(0)': 'http://axschema.org/contact/email',
                        'attributeList.attribute(1)': 'http://schema.openid.net/contact/fullname'
                    })
            
            personal_data = {}
            key_re = re.compile(r'response.personalData\((?P<index>\d+)\)\.(?P<name>.+)')
            for key in response.raw:
                m = re.match(key_re, key)
                if not m is None and m.group('name') == 'personalDataKey':
                    personal_data[response.get(key)] = response.get('response.personalData(%s).personalDataValue' % m.group('index'))
           
            store.paypal_email = personal_data['http://axschema.org/contact/email']
            store.save()
            return {}
        else:
            response = paypalAP.callPermissions('RequestPermissions',
                callback=self.request.build_absolute_uri(reverse('stores.create_store_done')),
                **{
                    'scope(0)': 'ACCESS_BASIC_PERSONAL_DATA',
                    'scope(1)':'REFUND'
                })
        return { 'paypal_url': paypalAP.generate_permissions_redirect_url(response.token) }


class ItemView(LoginRequiredMixin, DetailView):
    model = Item
    context_object_name = 'item'
    template_name = 'stores/item.j.html'

    def get_context_data(self, **kwargs):
        context = super(ItemView, self).get_context_data(**kwargs)

        request = self.request
        item = self.object

        context.update({
            'item_details_json': DetailItemResource().to_json(
                obj=item, request=request),
            'images_json': ItemImageResource().to_json(
                obj=item.images.all(), request=request),
        })

        return context


class ManageContactInformationView(LoginRequiredMixin, FormView):
    template_name = 'stores/manage/contact_information.j.html'
    form_class = ContactInformationForm
    
    def get_initial(self):
        return { 'country': 'AU' }

    def get_form_kwargs(self):
        kwargs = super(ManageContactInformationView, self).get_form_kwargs()
        kwargs.update({ 'instance': self.request.user.store })
        return kwargs

    def form_valid(self, form):
        form.save()
        return self.render_to_response(
                self.get_context_data(form=form,updated=True))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


class ManageItemsView(LoginRequiredMixin, TemplateView):
    template_name = 'stores/manage/items.j.html'

    def get_context_data(self, **kwargs):
        items_per_page = 4

        items = self.request.user.store.items.all()
        items_json = ItemResource().to_json(obj=items[:items_per_page],
                                            request=self.request)

        kwargs.update({
            'items_json': items_json,
            'items_total': items.count(),
            'items_per_page': items_per_page,
            'item_form': ItemCreationForm(),
            'image_form': ItemImageCreationForm()
        })
        return kwargs


class ManageDiscountsView(LoginRequiredMixin, TemplateView):
    template_name = 'stores/manage/discounts.j.html'

    def get_context_data(self, **kwargs):
        context = super(ManageDiscountsView, self).get_context_data(**kwargs)
        request = self.request

        discounts_json = DiscountResource().to_json(
                obj=Discount.objects.filter(store=request.user.store),
                request=request)

        context.update({
            'discounts_json': discounts_json,
            'discount_creation_form': DiscountCreationForm()
        })
        return context


class ManageDiscountGroupsView(LoginRequiredMixin, TemplateView):
    template_name = 'stores/manage/discount_groups.j.html'

    def get_context_data(self, **kwargs):
        context = super(ManageDiscountGroupsView, self).get_context_data(**kwargs)
        request = self.request

        discount_groups = DiscountGroup.objects.filter(
                discount__store=request.user.store)
        discount_groups_json = DiscountGroupResource().to_json(
                obj=discount_groups,
                request=request)
        
        discounts_json = DiscountResource().to_json(
                obj=Discount.objects.filter(store=request.user.store),
                request=request)
        
        items = request.user.store.items.all()
        items_json = ItemResource().to_json(
                obj=items, request=request)

        context.update({ 
            'discount_groups_json': discount_groups_json,
            'items_json': items_json,
            'discounts_json': discounts_json,
            'discount_group_form': DiscountGroupCreationForm()
        })
        return context



class ManageShippingRequests(LoginRequiredMixin, TemplateView):
    template_name = 'stores/manage/shipping.j.html'

    def get_context_data(self, **kwargs):
        context = super(ManageShippingRequests, self) \
                .get_context_data(**kwargs)
        request = self.request

        resource = PendingShippingRequestResource()
        shipping_requests = resource.apply_authorization_limits(
                request, resource._meta.queryset)

        context.update({
            'shipping_requests_json': resource.to_json(
                obj=shipping_requests,
                request=request)
        })
        return context


class ChangeStoreDesign(LoginRequiredMixin, UpdateView):
    form_class = StoreDesignForm
    model = StoreDesign
    template_name = 'stores/manage/change_shopdesign.j.html'
    
    def get_object(self, queryset=None):
        store = self.request.user.store 
        try:
            sd = store.design
        except self.model.DoesNotExist:
            sd = self.model.objects.create(store=store)
        return sd
    
    def get_success_url(self):
        return reverse('stores.design')

    def form_invalid(self, *args, **kwargs):
        messages.warning(self.request, _('Design is not saved!'))
        return super(ChangeStoreDesign, self).form_invalid(*args, **kwargs)
        
    def form_valid(self, *args, **kwargs):
        messages.success(self.request, _('Design saved successfully'))
        return super(ChangeStoreDesign, self).form_valid(*args, **kwargs)
