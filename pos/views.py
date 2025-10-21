from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, Http404, FileResponse
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .permissions import PERMISSION_LABELS, default_permissions
from .models import ManagerInvite, Shop, ShopManager, Product
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, View
from django.db.models import Sum
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth, TruncYear
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from . import utils
import barcode
from barcode.writer import ImageWriter
import io

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
    breadcrumbs = []

    def get_breadcrumbs(self):
        return [{"name": "Shops", "url": reverse("home")},
                {"name": self.shop.name, "url": reverse("dashboard", args=[self.shop.slug])}]

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
            'active_page': self.active_page,
            'breadcrumbs': self.get_breadcrumbs()
        })
        return context
        
class ProductBarcodeDownloadView(ShopAccessMixin, View):
    def get(self, request, *args, **kwargs):
        product_id = kwargs.get("pk")
        product = get_object_or_404(Product, pk=product_id, shop=self.shop)
        
        barcode_class = barcode.get_barcode_class('code128')
        barcode_image = barcode_class(str(product.barcode), writer=ImageWriter())
        
        buffer = io.BytesIO()
        barcode_image.write(buffer)
        buffer.seek(0)
        
        filename = f"{product.name}_barcode.png"
        return FileResponse(buffer, as_attachment=True, filename=filename)
        
    

class DashboardView(ShopAccessMixin, TemplateView):
    template_name = "pos/shop/dashboard.html"
    active_page = 'dashboard' # For context
    
class ProductView(ShopAccessMixin, ListView):
    template_name = "pos/shop/products.html"
    active_page = 'products' # For context
    required_perms = ['can_view_products']
    paginate_by = 10
    def get_queryset(self):
        return Product.objects.filter(shop=self.shop)
    
    def get_breadcrumbs(self):
        base = super().get_breadcrumbs()
        base.extend([{"name": "Products", "url": None}])
        return base
    
class ProductDetailView(ShopAccessMixin, DetailView):
    template_name = "pos/shop/product_details.html"
    active_page = "products"
    required_perms = ["can_view_products"]
    model = Product
    context_object_name = "product"
    
    def get_breadcrumbs(self):
        base = super().get_breadcrumbs()
        base.extend([{"name": "Products", "url": reverse('products', args=[self.shop.slug])},
                     {"name": self.product.name, "url": None}])
        return base

    def get_queryset(self):
        return Product.objects.filter(shop=self.shop)

    def get_object(self, queryset=None):
        self.product = super().get_object(queryset)
        product = self.product

        # Normalize discount
        product.discount_percentage = Decimal(product.discount_percentage).normalize()

        # Attach hex color
        product.category.hex_code = utils.CATEGORY_COLORS_MAPPING[product.category.color]

        # Reference current time once (for performance + clarity)
        now = timezone.now()
        start_dates = {
            "year": now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            "month": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            "week": (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
            "day": now.replace(hour=0, minute=0, second=0, microsecond=0),
        }

        # Aggregate all-time
        aggregates = {
            "all_time": product.sale_products.aggregate(
                total_quantity=Sum("quantity"),
                total_revenue=Sum("sub_total"),
            )
        }

        # Aggregate for each period
        for period, start_date in start_dates.items():
            aggregates[period] = product.sale_products.filter(
                sale__created_at__gte=start_date
            ).aggregate(
                total_quantity=Sum("quantity"),
                total_revenue=Sum("sub_total"),
            )

        # Assign results to product
        for period, data in aggregates.items():
            total_qty = data["total_quantity"] or 0
            total_rev = Decimal(data["total_revenue"] or 0).normalize()
            setattr(product, f"{period}_sales", total_qty)
            setattr(product, f"{period}_revenue", total_rev)
            
        
        product.sales_data = [
            ("All Time", product.all_time_sales),
            ("This Year", product.year_sales),
            ("This Month", product.month_sales),
            ("This Week", product.week_sales),
            ("Today", product.day_sales),
        ]

        product.revenue_data = [
            ("All Time", product.all_time_revenue),
            ("This Year", product.year_revenue),
            ("This Month", product.month_revenue),
            ("This Week", product.week_revenue),
            ("Today", product.day_revenue),
        ]

        return product
        