from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, Http404, FileResponse, JsonResponse
from django.urls import reverse
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm
from .forms import ProductForm, ProductVariantForm, ProductVariantFormSet
from django.contrib.auth.decorators import login_required
from django.db.models import DecimalField
from .permissions import PERMISSION_LABELS, default_permissions
from .models import ManagerInvite, Shop, ShopManager, Product, Category, ProductVariant, SaleProduct
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView, View
from django.db.models import Sum, Q, F
from django.db import transaction
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
    

class GetVariantSnippetView(ShopAccessMixin, View):
    def get(self, request, *args, **kwargs):
        form = ProductVariantForm()
        return render(request, "pos/shop/partials/variant_form.html", {"form": form})
        
class ProductBarcodeDownloadView(ShopAccessMixin, View):
    def get(self, request, *args, **kwargs):
        product_variant_id = kwargs.get("pk")
        product = get_object_or_404(ProductVariant, pk=product_variant_id, product__shop=self.shop)
        
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
    context_object_name = "product_list"
    paginate_by = 50
    def get_queryset(self):
        products = Product.objects.filter(shop=self.shop, product_variants__is_deleted=False).distinct()
        print(products.first().pk)

        # # Search
        # search = self.request.GET.get("search")
        # if search:
        #     products = products.filter(Q(name__icontains=search) | Q(barcode__icontains=search))
            
        
        # # Category
        # category = self.request.GET.get("category")
        # if category:
        #     products = products.filter(category__name__iexact=category)
        
        # # Stock Filter
        # stock = self.request.GET.get("stock")
        # if stock:
        #     if stock.lower() == 'out':
        #         products = products.filter(stock_quantity=0)
        #     elif stock.lower() == 'low':
        #         products = products.filter(stock_quantity__lte=F("reorder_point"), stock_quantity__gt=0)
        #     elif stock.lower() == 'high':
        #         products = products.filter(stock_quantity__gt=F("reorder_point"))
                
        
        # # Sorting
        # sort = self.request.GET.get("sort")
        # if sort == "price_asc":
        #     products = products.order_by("price_after_discount")
        # elif sort == "price_desc":
        #     products = products.order_by("-price_after_discount")
        # elif sort == "original_price_asc":
        #     products = products.order_by("price")
        # elif sort == "original_price_desc":
        #     products = products.order_by("-price")
        # elif sort == "discount_desc":
        #     products = products.order_by("-discount_percentage")
        # elif sort == "stock_asc":
        #     products = products.order_by("stock_quantity")
        # elif sort == "stock_desc":
        #     products = products.order_by("-stock_quantity")
        # elif sort == "reorder_asc":
        #     products = products.order_by("reorder_point")
        # elif sort == "reorder_desc":
        #     products = products.order_by("-reorder_point")
        
        
        
        
        for product in products:
            product.hex_code = utils.CATEGORY_COLORS_MAPPING[product.category.color] # For context
        
        return products
    
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

        # --- Normalize discounts for all variants ---
        for variant in product.product_variants.filter(is_deleted=False):
            variant.discount_percentage = Decimal(variant.discount_percentage).normalize()

        # --- Attach category hex code ---
        product.category.hex_code = utils.CATEGORY_COLORS_MAPPING.get(product.category.color, "#000000")

        # --- Prepare time periods ---
        now = timezone.now()
        start_dates = {
            "year": now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            "month": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            "week": (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0),
            "day": now.replace(hour=0, minute=0, second=0, microsecond=0),
        }

        # --- Base QuerySet: all sale products for this product's variants ---
        sale_products_qs = SaleProduct.objects.filter(product__product=product)

        # --- Aggregate all-time ---
        aggregates = {
            "all_time": sale_products_qs.aggregate(
                total_quantity=Sum("quantity"),
                total_revenue=Sum("sub_total", output_field=DecimalField()),
            )
        }

        # --- Aggregate per period ---
        for period, start_date in start_dates.items():
            aggregates[period] = sale_products_qs.filter(
                sale__created_at__gte=start_date
            ).aggregate(
                total_quantity=Sum("quantity"),
                total_revenue=Sum("sub_total", output_field=DecimalField()),
            )

        # --- Assign results to product for template use ---
        for period, data in aggregates.items():
            total_qty = data["total_quantity"] or 0
            total_rev = Decimal(data["total_revenue"] or 0).normalize()
            setattr(product, f"{period}_sales", total_qty)
            setattr(product, f"{period}_revenue", total_rev)

        # --- Prepare lists for charts or templates ---
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
            
        
class ProductUpdateView(ShopAccessMixin, UpdateView):
    template_name = 'pos/shop/product_update.html'
    model = Product
    form_class = ProductForm
    active_page = "products"
    required_perms = ["can_edit_products"]
    
    def get_form(self, form_class=None):
        form =  super().get_form(form_class)
        form.fields["category"].queryset = Category.objects.filter(shop=self.shop)
        return form
    
    def form_valid(self, form):
        messages.success(self.request, "Product updated successfully!")
        if self.request.POST.get('delete_image') == 'true':
            if self.object.image:
                self.object.image.delete(save=False)
            self.object.image = None
        return super().form_valid(form)
        
    def get_queryset(self):
        return Product.objects.filter(shop=self.shop)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["shop"] = self.shop
        return kwargs
    
    def get_success_url(self):
        return reverse("product_details", args=[self.shop.slug, self.object.pk])
    
    def get_breadcrumbs(self):
        base = super().get_breadcrumbs()
        base.extend([{"name": "Products", "url": reverse('products', args=[self.shop.slug])},
                     {"name": self.object.name, "url": reverse("product_details", args=[self.shop.slug, self.object.pk])},
                     {"name": "Edit", "url": None}])
        return base
    
    
class ProductCreateView(ShopAccessMixin, TemplateView):
    template_name = 'pos/shop/product_create.html'
    active_page = 'products'
    model = Product
    form_class = ProductForm
    required_perms = ['can_create_products']
    
    def get_success_url(self):
        return reverse('product_details', args=[self.shop.slug, self.object.pk]) # Go to created product
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        form = self.form_class(shop=self.shop)
        context["product_form"] = form
        context["variant_formset"] = ProductVariantFormSet()
        return context

    def post(self, request, *args, **kwargs):
        product_form = ProductForm(request.POST, shop=self.shop)
        variant_formset = ProductVariantFormSet(request.POST, request.FILES)

        if product_form.is_valid():
            # Create product object but don't save yet.
            product = product_form.save(commit=False)
            # We need to asign shop before checking if formset is valid cuz it will give error variant.product has no shop.
            product.shop = self.shop             
            variant_formset.instance = product
            if variant_formset.is_valid():
                with transaction.atomic():
                    product.save()
                    variant_formset.save()
                messages.success(request, "Product created with variants")
                return redirect("product_details", self.shop.slug, product.pk)
        context = self.get_context_data(**kwargs)
        context.update({"product_form": product_form, "variant_formset": variant_formset})
        return render( request, self.template_name, context)
            
        if product_form.is_valid() and variant_formset.is_valid():
            with transaction.atomic():
                product = product_form.save()
                
                variant_formset.instance = product
                variant_formset.save()

            messages.success(request, "Product created with variants")
            return redirect("product_details", self.shop.slug, product.pk)
        return render(request, self.template_name, {"product_form": product_form, "variant_formset": variant_formset})
        
    def get_breadcrumbs(self):
        base = super().get_breadcrumbs()
        base.extend([{"name": "Products", "url": reverse('products', args=[self.shop.slug])},
                     {"name": "Create", "url": None}])
        return base
    
    
class ProductDeleteView(ShopAccessMixin, View):
    def post(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        product = get_object_or_404(Product, pk=pk, shop=self.shop)
        product.soft_delete()

        messages.success(self.request, "Product deleted successfully!")
        return redirect(reverse('products', args=[self.shop.slug]))