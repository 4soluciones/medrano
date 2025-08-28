from django.contrib.auth.forms import AuthenticationForm


class FormLogin(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(FormLogin, self).__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['id'] = 'username'
        self.fields['username'].widget.attrs['class'] = 'form-control input-shadow'
        self.fields['username'].widget.attrs['type'] = 'text'
        self.fields['username'].widget.attrs['placeholder'] = 'Usuario'
        self.fields['password'].widget.attrs['id'] = 'password'
        self.fields['password'].widget.attrs['class'] = 'form-control input-shadow'
        self.fields['password'].widget.attrs['placeholder'] = 'Contraseña'
        self.fields['password'].widget.attrs['type'] = 'password'
