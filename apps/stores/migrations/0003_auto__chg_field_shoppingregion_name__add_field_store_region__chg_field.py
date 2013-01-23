# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'ShoppingRegion.name'
        db.alter_column('stores_shoppingregion', 'name', self.gf('django.db.models.fields.CharField')(max_length=100))

        # Adding field 'Store.region'
        db.add_column('stores_store', 'region', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['stores.ShoppingRegion'], null=True), keep_default=False)

        # Changing field 'Store.name'
        db.alter_column('stores_store', 'name', self.gf('django.db.models.fields.CharField')(max_length=100))


    def backwards(self, orm):
        
        # Changing field 'ShoppingRegion.name'
        db.alter_column('stores_shoppingregion', 'name', self.gf('django.db.models.fields.CharField')(max_length=256))

        # Deleting field 'Store.region'
        db.delete_column('stores_store', 'region_id')

        # Changing field 'Store.name'
        db.alter_column('stores_store', 'name', self.gf('django.db.models.fields.CharField')(max_length=256))


    models = {
        'stores.shoppingregion': {
            'Meta': {'object_name': 'ShoppingRegion'},
            'center': ('django.contrib.gis.db.models.fields.PointField', [], {'spatial_index': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'zoom': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'stores.store': {
            'Meta': {'object_name': 'Store'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stores.ShoppingRegion']", 'null': 'True'})
        }
    }

    complete_apps = ['stores']
