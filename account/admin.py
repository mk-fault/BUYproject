from django.contrib import admin
from .models import AccountModel
from django.contrib.auth.admin import UserAdmin

# Register your models here.
admin.site.register(AccountModel, UserAdmin)
