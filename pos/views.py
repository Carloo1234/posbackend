from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm

# Create your views here.
@require_http_methods(["GET"])
def index(request):
    if not request.user.is_authenticated: 
        # Not authenticated
        return redirect('login')
    else: 
        # Authenticated
        return redirect('home')
    
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
    
class Logout(LogoutView):
    template_name='pos/auth/logout.html'


    
@require_http_methods(["GET"])
def home(request):
    return redirect('owned_shops')

@require_http_methods(["GET", "POST"])
def owned_shops(request):
    if not request.user.is_authenticated:
        return redirect('login')
    owned_shops = request.user.shops.all()
    shop_managers = request.user.shops_managed.all()
    managed_shops = []
    for shop_manager in shop_managers:
        managed_shops.append(shop_manager.shop)
    
    return render(request, "pos/home/owned_shops.html", {'owned_shops': owned_shops,
                                              'managed_shops': managed_shops
                                              })

def managed_shops(request):
    return render(request, "pos/home/managed_shops.html")

def manager_invites(request):
    return render(request, "pos/home/manager_invites.html")

def create_shop(request):
    return HttpResponse("In construction", status=200)

    