# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'SocialTag', fields ['item', 'user']
        db.delete_unique('cart_socialtag', ['item_id', 'user_id'])

        # Removing unique constraint on 'PersonalTag', fields ['item', 'user']
        db.delete_unique('cart_personaltag', ['item_id', 'user_id'])

        # Adding model 'Transaction'
        db.create_table('cart_transaction', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('is_approved', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('preapproval_key', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
        ))
        db.send_create_signal('cart', ['Transaction'])

        # Adding field 'PersonalTag.transaction'
        db.add_column('cart_personaltag', 'transaction', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cart.Transaction'], unique=True, null=True), keep_default=False)

        # Adding unique constraint on 'PersonalTag', fields ['item', 'transaction', 'user']
        db.create_unique('cart_personaltag', ['item_id', 'transaction_id', 'user_id'])

        # Adding field 'SocialTag.transaction'
        db.add_column('cart_socialtag', 'transaction', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['cart.Transaction'], unique=True, null=True), keep_default=False)

        # Adding unique constraint on 'SocialTag', fields ['item', 'buy', 'user', 'transaction']
        db.create_unique('cart_socialtag', ['item_id', 'buy_id', 'user_id', 'transaction_id'])

        # Adding field 'SocialBuy.store'
        db.add_column('cart_socialbuy', 'store', self.gf('django.db.models.fields.related.ForeignKey')(default=1, related_name='social_buys', to=orm['stores.Store']), keep_default=False)

        # Adding field 'SocialBuy.is_active'
        db.add_column('cart_socialbuy', 'is_active', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Removing unique constraint on 'SocialTag', fields ['item', 'buy', 'user', 'transaction']
        db.delete_unique('cart_socialtag', ['item_id', 'buy_id', 'user_id', 'transaction_id'])

        # Removing unique constraint on 'PersonalTag', fields ['item', 'transaction', 'user']
        db.delete_unique('cart_personaltag', ['item_id', 'transaction_id', 'user_id'])

        # Deleting model 'Transaction'
        db.delete_table('cart_transaction')

        # Deleting field 'PersonalTag.transaction'
        db.delete_column('cart_personaltag', 'transaction_id')

        # Adding unique constraint on 'PersonalTag', fields ['item', 'user']
        db.create_unique('cart_personaltag', ['item_id', 'user_id'])

        # Deleting field 'SocialTag.transaction'
        db.delete_column('cart_socialtag', 'transaction_id')

        # Adding unique constraint on 'SocialTag', fields ['item', 'user']
        db.create_unique('cart_socialtag', ['item_id', 'user_id'])

        # Deleting field 'SocialBuy.store'
        db.delete_column('cart_socialbuy', 'store_id')

        # Deleting field 'SocialBuy.is_active'
        db.delete_column('cart_socialbuy', 'is_active')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'cart.personaltag': {
            'Meta': {'unique_together': "(('user', 'item', 'transaction'),)", 'object_name': 'PersonalTag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'personal_tags'", 'to': "orm['stores.Item']"}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'transaction': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cart.Transaction']", 'unique': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'personal_tags'", 'to': "orm['auth.User']"})
        },
        'cart.socialbuy': {
            'Meta': {'object_name': 'SocialBuy'},
            'finish_date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'social_buys'", 'to': "orm['stores.Store']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'social_buys'", 'to': "orm['auth.User']"})
        },
        'cart.socialtag': {
            'Meta': {'unique_together': "(('user', 'item', 'buy', 'transaction'),)", 'object_name': 'SocialTag'},
            'buy': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tags'", 'to': "orm['cart.SocialBuy']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'social_tags'", 'to': "orm['stores.Item']"}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'transaction': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['cart.Transaction']", 'unique': 'True', 'null': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'social_tags'", 'to': "orm['auth.User']"})
        },
        'cart.transaction': {
            'Meta': {'object_name': 'Transaction'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'preapproval_key': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'stores.category': {
            'Meta': {'object_name': 'Category'},
            'icon': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'marker': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'stores.item': {
            'Meta': {'object_name': 'Item'},
            'description': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'discount': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_out_of_stock': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '2'}),
            'quantity': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'store': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': "orm['stores.Store']"})
        },
        'stores.shoppingregion': {
            'Meta': {'object_name': 'ShoppingRegion'},
            'center': ('django.contrib.gis.db.models.fields.PointField', [], {'spatial_index': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'zoom': ('django.db.models.fields.PositiveSmallIntegerField', [], {})
        },
        'stores.store': {
            'Meta': {'object_name': 'Store'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stores.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'region': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['stores.ShoppingRegion']", 'null': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'store'", 'unique': 'True', 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['cart']