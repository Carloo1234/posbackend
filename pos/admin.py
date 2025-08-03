from django.contrib import admin
from .models import User, Shop, ShopManager, ManagerInvite, Product, Sale, SaleProduct

# Register your models here.

admin.site.register(User)
admin.site.register(Shop)
admin.site.register(ShopManager)
admin.site.register(ManagerInvite)
admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(SaleProduct)