from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
@require_http_methods(["GET"])
def index(request):
    if not request.user.is_authenticated: 
        # Not authenticated
        return redirect('login')
    else: 
        # Authenticated
        return redirect('shops')
            

@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == "GET":
        return render(request, 'pos/auth/login.html')
    
class CustomLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'focus:outline-none focus:border-2 focus:border-primary text-sm rounded-sm px-3 py-2 mb-5 w-full border border-border',
        })
        self.fields['password'].widget.attrs.update({
            'class': 'focus:outline-none focus:border-2 focus:border-primary text-sm rounded-sm px-3 py-2 mb-5 w-full border border-border',
        })
    
class Login(LoginView):
    template_name='pos/auth/login.html'
    redirect_authenticated_user = True
    success_url = "/"
    
    def get_success_url(self):  
        return self.success_url
    authentication_form = CustomLoginForm

@require_http_methods(["GET"])
def shops(request):
    return render(request, "pos/shops.html", {'shops': request.user.shops.all()})

    