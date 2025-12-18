from django.contrib import admin
from .models import User, Shop, ShopManager, ManagerInvite, Product, Sale, SaleProduct, Category, ProductVariant, ProductAttribute, ProductAttributeValue, ProductVariantAttributeValue

# Register your models here.

admin.site.register(User)
admin.site.register(Shop)
admin.site.register(ShopManager)
admin.site.register(ManagerInvite)
admin.site.register(Product)
admin.site.register(Sale)
admin.site.register(SaleProduct)
admin.site.register(Category)
admin.site.register(ProductAttribute)



class ProductVariantAttributeValueInline(admin.TabularInline):
    model = ProductVariantAttributeValue
    extra = 1 # or however many empty forms you want to display

# Register your other models with the custom admin classes
@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    inlines = [
        ProductVariantAttributeValueInline,
    ]

@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    inlines = [
        ProductVariantAttributeValueInline,
    ]