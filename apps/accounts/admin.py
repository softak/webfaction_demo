from django.contrib import admin
from accounts.models import EmailConfirmation


class EmailConfirmationAdmin(admin.ModelAdmin):
    list_display = ['email', 'last_sent']
admin.site.register(EmailConfirmation, EmailConfirmationAdmin)
