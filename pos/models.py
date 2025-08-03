from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from .utils import generate_ean13_without_check, is_valid_ean13
from django.utils import timezone

# Create your models here.



class User(AbstractUser):
    full_name = models.CharField(max_length=100)
    pfp = models.ImageField(upload_to="pfps/", null=True, blank=True)
    can_create_shops = models.BooleanField(blank=True, default=True)
    
    def get_pfp_url(self):
        if self.pfp:
            return self.pfp.url
        return "/media/pfps/defaultpfp.jpg"
    
    def __str__(self):
        return f'{self.full_name} ({self.pk})'
    

    
class Shop(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="shops")
    managers = models.ManyToManyField(User, through='ShopManager')
    created_at = models.DateTimeField(auto_now_add=True)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    tax_percentage = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    currency_code = models.CharField(max_length=10) # Examples: EGP, $, ect...
    
    def get_logo_url(self):
        if self.logo:
            return self.logo.url
        return "/media/logos/defaultlogo.jpg"
    
    def __str__(self):
        return f'{self.name} ({self.pk})'
    
class Permissions(models.Model):
    can_view_products = models.BooleanField(default=False)
    can_edit_products = models.BooleanField(default=False)

    can_view_sales = models.BooleanField(default=False)
    can_edit_sales = models.BooleanField(default=False)

    can_view_managers = models.BooleanField(default=False)
    can_edit_managers = models.BooleanField(default=False)

    class Meta:
        abstract = True
    
    
class ShopManager(Permissions):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shops_managed')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.user} is managing {self.shop}'
    

class ManagerInvite(Permissions):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invites_recieved")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE)
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="invites_sent", blank=True)
    created_at = models.DateTimeField(auto_now_add=True) # for expiry date
    
    def accept(self):
        ShopManager.objects.create(user=self.user, shop=self.shop,
                                   can_view_products=self.can_view_products,
                                   can_edit_products=self.can_edit_products,
                                   can_view_sales=self.can_view_sales,
                                   can_edit_sales=self.can_edit_sales,
                                   can_view_managers=self.can_view_managers,
                                   can_edit_managers=self.can_edit_managers)
        self.delete()
    
    def decline(self):
        self.delete()
    
    def __str__(self):
        return f'{self.sent_by} is inviting {self.user} to manage {self.shop}'
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'shop'], name='unique_user_shop_invite')
        ]
    

class Product(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    barcode = models.CharField(max_length=13)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.IntegerField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    price_after_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True)
    
    is_deleted = models.BooleanField(default=False)
    marked_for_deletion_at = models.DateTimeField(null=True, blank=True)
    
    def soft_delete(self): # For syncing with offline POS terminal.
        self.is_deleted = True
        self.marked_for_deletion_at = timezone.now()
    
    
    def clean(self):
        errors = {}

        if not is_valid_ean13(self.barcode):
            errors['barcode'] = 'Invalid barcode check digit.'

        if self.discount_percentage > 100:
            errors['discount_percentage'] = 'Discount percentage can\'t be bigger than 100%.'

        if self.discount_percentage < 0:
            errors['discount_percentage'] = 'Discount percentage can\'t be smaller than 0%.'
            
        if self.price < 0:
            errors['price'] = 'Price can\'t be smaller than 0.'

        if errors:
            raise ValidationError(errors)

            
        
    def save(self, *args, **kwargs):
        self.full_clean()
        self.price_after_discount = ((100-self.discount_percentage)/100)*self.price
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.name} - {self.price_after_discount}{self.shop.currency_code}'
        
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['shop', 'barcode'], name='unique_shop_barcode_product')
            ]
        
class Sale(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales')
    added_by = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    total_after_shop_discount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    total_after_shop_tax = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    
    
    def calculate_total_price(self):
        self.total_amount = 0
        for sale in self.sale_products.all():
            self.total_amount += sale.sub_total
        
        self.total_after_shop_discount = ((100-self.shop.discount_percentage)/100)*self.total_amount
        self.total_after_shop_tax = ((self.shop.tax_percentage+100)/100) * self.total_after_shop_discount
        
        self.save()
    
    def __str__(self):
        return f'{self.pk} - {self.total_after_shop_tax}{self.shop.currency_code}'
    
class SaleProduct(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='sale_products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sale_products')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    
    def save(self, *args, **kwargs):
        self.sub_total = self.quantity * self.unit_price
        self.sale.calculate_total_price()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.quantity} {self.product}'
    
    
    
