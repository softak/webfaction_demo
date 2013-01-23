# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'PasswordReset'
        db.delete_table('accounts_passwordreset')

        # Deleting model 'EmailConfirmation'
        db.delete_table('accounts_emailconfirmation')


    def backwards(self, orm):
        
        # Adding model 'PasswordReset'
        db.create_table('accounts_passwordreset', (
            ('last_sent', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='password_resets', to=orm['auth.User'])),
        ))
        db.send_create_signal('accounts', ['PasswordReset'])

        # Adding model 'EmailConfirmation'
        db.create_table('accounts_emailconfirmation', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('last_sent', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='email_confirmations', to=orm['auth.User'])),
            ('key', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
        ))
        db.send_create_signal('accounts', ['EmailConfirmation'])


    models = {
        
    }

    complete_apps = ['accounts']
