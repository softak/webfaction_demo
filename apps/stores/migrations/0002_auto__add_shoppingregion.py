# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ShoppingRegion'
        db.create_table('stores_shoppingregion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('center', self.gf('django.contrib.gis.db.models.fields.PointField')(spatial_index=False)),
            ('zoom', self.gf('django.db.models.fields.PositiveSmallIntegerField')()),
        ))
        db.send_create_signal('stores', ['ShoppingRegion'])


    def backwards(self, orm):
        
        # Deleting model 'ShoppingRegion'
        db.delete_table('stores_shoppingregion')


    models = {
        'stores.shoppingregion': {
            'Meta': {'object_name': 'ShoppingRegion'},
            'center': ('django.contrib.gis.db.models.fields.PointField', [], {'spatial_index': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'zoom': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'stores.store': {
            'Meta': {'object_name': 'Store'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        }
    }

    complete_apps = ['stores']
