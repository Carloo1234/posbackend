from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .permissions import PERMISSION_LABELS, default_permissions
from .models import ManagerInvite, Shop, ShopManager, Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView

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

def get_shop_and_role(request, slug):
    shop = Shop.objects.filter(slug=slug).first()
    if not shop:
        return None, None, None  # Shop not found

    if request.user.shops.filter(pk=shop.pk).exists():
        return shop, 'owner', None

    shop_manager = request.user.shops_managed.filter(shop=shop).first()
    if shop_manager:
        return shop, 'manager', shop_manager

    return shop, None, None  # Shop exists but no access

@login_required
@require_http_methods(["GET"])
def shop_dashboard(request, slug): # /shops/<str:slug>/dashboard
    shop, role, shop_manager = get_shop_and_role(request, slug)

    if not shop:
        raise Http404
        # return render(request, "pos/errors/404.html", {
        #     'message': 'Shop not found. Make sure you have the correct URL.'
        # }, status=404)

    if not role:  # Means no permission
        return render(request, 'pos/errors/403.html', status=403)

    return render(request, "pos/shop/dashboard.html", {
        'shop': shop,
        'active_page': 'dashboard',
        'isOwner': role == 'owner',
        'shop_manager': shop_manager
    })
    
@login_required
@require_http_methods(["GET"])
def shop_products(request, slug): # /shops/<str:slug>/products
    shop, role, shop_manager = get_shop_and_role(request, slug)

    if not shop:
        return render(request, "pos/errors/404.html", {
            'message': 'Shop not found. Make sure you have the correct URL.'
        }, status=404)

    if not role:  # Means no permission
        return render(request, 'pos/errors/403.html', status=403)

    return render(request, "pos/shop/products.html", {
        'shop': shop,
        'active_page': 'products',
        'isOwner': role == 'owner',
        'shop_manager': shop_manager
    })
    
    
class ShopAccessMixin(LoginRequiredMixin):
    required_perms = []
    active_page = None

    def dispatch(self, request, *args, **kwargs):
        slug = self.kwargs.get("slug")
        shop = get_object_or_404(Shop, slug=slug)
        
        # Owner
        if request.user.shops.filter(pk=shop.pk).exists():
            self.shop = shop
            self.isOwner = True
            self.shop_manager = None
            return super().dispatch(request, *args, **kwargs)
        
        # Manager
        shop_manager = request.user.shops_managed.filter(shop=shop).first()
        if shop_manager:
            # Has permissions
            has_perm = True
            for perm in self.required_perms:
                if not shop_manager.has_permission(perm):
                    has_perm = False
                    
            if has_perm:
                self.shop = shop
                self.isOwner = False
                self.shop_manager = shop_manager
                return super().dispatch(request, *args, **kwargs)
        # Not allowed
        raise PermissionDenied("User doesnt have permission.")
    
    def get_context_data(self, **kwargs):
        context =  super().get_context_data(**kwargs)
        context.update({
            'shop': self.shop,
            'isOwner': self.isOwner,
            'shop_manager': self.shop_manager,
            'active_page': self.active_page
        })
        return context
        
        
class DashboardView(ShopAccessMixin, TemplateView):
    template_name = "pos/shop/dashboard.html"
    active_page = 'dashboard' # For context
    
class ProductView(ShopAccessMixin, ListView):
    template_name = "pos/shop/products.html"
    active_page = 'products' # For context
    def get_queryset(self):
        return Product.objects.filter(shop=self.shop)