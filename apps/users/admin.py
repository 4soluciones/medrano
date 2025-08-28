from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from apps.users.models import CustomUser


@admin.register(CustomUser)
class UserAdmin(BaseUserAdmin):
    pass
