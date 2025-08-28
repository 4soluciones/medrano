from django.urls import path, include
from django.contrib.auth.decorators import login_required
from apps.users.views import *

urlpatterns = [
    path('get_user_logged/', login_required(get_user_logged), name='get_user_logged'),
]