from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .permissions import PERMISSION_LABELS
from .models import ManagerInvite, Shop

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


@login_required
@require_http_methods(["GET"])
def home(request):
    return redirect('owned_shops')

@login_required
@require_http_methods(["GET", "POST"])
def owned_shops(request):
    if not request.user.is_authenticated:
        return redirect('login')
    owned_shops = request.user.shops.all()
    
    return render(request, "pos/home/owned_shops.html", {'owned_shops': owned_shops,})

@login_required
@require_http_methods(["GET"])
def managed_shops(request):
    shop_managers = request.user.shops_managed.all()
    managed_shops = []
    for shop_manager in shop_managers:
        managed_shops.append(shop_manager.shop)
    return render(request, "pos/home/managed_shops.html", {'managed_shops': managed_shops})
    
@login_required
@require_http_methods(["GET", "POST"])
def manager_invites(request):
    if request.method == "POST":
        invite_id = request.POST.get("invite_id")
        action = request.POST.get("action")
        try:
            invite = request.user.invites_recieved.get(id=invite_id)
            
        except ManagerInvite.DoesNotExist:
            messages.error(request, "Invite not found.")
            return redirect("manager_invites")
        
        if action == "accept":
            invite.accept()
            messages.success(request, f"You are now managing {invite.shop.name}.")
        elif action == "decline":
            invite.decline()
            messages.info(request, f"Declined invite for {invite.shop.name}.")
        else:
            messages.error(request, "Invalid action.")
        
        return redirect("manager_invites")
        
    shop_invites = request.user.invites_recieved.all()
    context = {
        "invites": shop_invites,
        "permission_labels": PERMISSION_LABELS,
    }
    return render(request, "pos/home/manager_invites.html", context)

@login_required
def create_shop(request):
    return HttpResponse("In construction", status=200)

@login_required
@require_http_methods(["GET"])
def shop_dashboard(request, slug): # /shops/<str:slug>/dashboard
    if not Shop.objects.filter(slug=slug).exists():
        # Shop doesn't exist
        return render(request, "pos/errors/404.html", {'message': 'shop not found. Make sure you have the correct url.'}, status=404)
    shop = Shop.objects.get(slug=slug)
    managed_and_owned_shops = request.user.shops.all() | Shop.objects.filter(id__in=request.user.shops_managed.values_list("shop_id", flat=True))
    if not managed_and_owned_shops.filter(pk=shop.pk).exists():
        return render(request, "pos/errors/403.html")
    return render(request, "pos/shop/dashboard.html")
    
