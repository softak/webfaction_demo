# -*- coding: utf-8 -*-
import os
from lettuce import step, before, after, world
from funfactory.manage import path
from django.core.management import call_command
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from stores.models import ShopDesign

@after.each_feature
def logout_user(results):
    call_command('flush', interactive=False, verbosity=0)
    world.client.logout()
    
def load_data():
    fixture_path = path('apps/stores/fixtures/sample.json')
    call_command('loaddata', fixture_path, interactive=False, verbosity=0)
        
def reset_pswd():
    u = User.objects.get(username__exact='books')
    u.set_password('books')
    u.save()
    return u
    
@step(u'Just look at the clean store')
def just_look_at_the_clean_store(step):
    load_data()
    reset_pswd()
    res = world.client.login(username='books@sd.com', password='books')
    world.store_design_url = reverse('stores.design')
    result = world.client.get(world.store_design_url)
    
    assert result.status_code == 200, \
        'Status code must be 200, not a %d' % result.status_code 
    assert 'Change shop background' in result.content
    
@step(u'Given I whant to set a "([^"]*)" color, and "([^"]*)" image "([^"]*)"')
def given_i_whant_to_set_a_group1_color_and_group2_image_group3(step, hex, rep, img):
    fimg   = open(path(img))
    is_rep = False if 'no' in rep else True
    data   = {'background_image': fimg, 
              'is_repeated'     : is_rep, 
              'background_color': hex}
    resp   =  world.client.post(world.store_design_url, data)
    assert resp.status_code == 302, \
        'Status code must be 302, not a %d' % resp.status_code 
    
    world.user = User.objects.get(username__exact='books')
    sd = world.user.store.shop_design
    assert os.path.basename(img).split('.')[0] in sd.background_image.url, \
                                    'There is no img at the model instance'
    assert sd.is_repeated == is_rep, 'Wrong the repeated trigger'
    assert sd.background_color == hex, 'Wrong color at the model instance'

@step(u'Then I see in a store profile "([^"]*)"')
def then_i_see_in_a_store_profile_group1(step, bkg_style):
    world.store_view_url = reverse('stores.view_store', 
                           args=(world.user.store.id,))
    response = world.client.get(world.store_view_url)
    
    assert response.status_code == 200, \
         'Status code must be 200, not a %d' % response.status_code 
    assert bkg_style in response.content, 'Wrong style line.'
   
@step(u'Then I whant to clear the background')
def then_i_whant_to_clear_the_background(step):
    data   = {'background_image-clear': True,
              'is_repeated'     : False, 
              'background_color': '#FFFFFF'}
    resp   =  world.client.post(world.store_design_url, data)
    assert resp.status_code == 302, \
        'Status code must be 302, not a %d' % resp.status_code 
    
@step(u'Then I see in a store profile nothing!')
def then_i_see_in_a_store_profile_nothing(step):
    sd = ShopDesign.objects.get(store=world.user.store)
    assert not sd.background_image, 'Background image must be clear'
    assert not sd.is_repeated,      'Repeat field must be false'
    assert sd.background_color == '#FFFFFF', 'Background color must be #FFFFFF'
    
    response = world.client.get(world.store_view_url)
    assert response.status_code == 200, \
         'Status code must be 200, not a %d' % response.status_code 
    assert 'style="background:#FFFFFF;"' in response.content, 'Wrong style line.'

    
