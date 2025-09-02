from http import HTTPStatus
from django.contrib.auth.hashers import make_password
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.generic import ListView, CreateView, UpdateView
from django.views.generic.edit import FormView
from django.contrib.auth import login, logout, authenticate
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from .forms import FormLogin
from django.shortcuts import render, redirect


# Create your views here.
class Login(FormView):
    template_name = 'login.html'
    form_class = FormLogin
    success_url = reverse_lazy('home')

    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(self.get_success_url())
        else:
            return super(Login, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super(Login, self).form_valid(form)

    def form_invalid(self, form):
        # Verificar si el usuario existe pero está inactivo
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user and not user.is_active:
                # Usuario existe pero está inactivo
                form.add_error(None, 'Usuario inactivo. Contacte con administración.')
            else:
                # Usuario o contraseña incorrectos
                form.add_error(None, 'Usuario o contraseña incorrectos')
        
        return super().form_invalid(form)


def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/accounts/login/')


def get_user_logged(request):
    return JsonResponse({
            'userID': request.user.id,
            'status': 'OK'
        }, status=HTTPStatus.OK)