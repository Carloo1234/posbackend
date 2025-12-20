from django import forms
from django.forms import inlineformset_factory
from .models import ProductVariant, Category, Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-input"}),
            "category": forms.Select(attrs={"class": "form-select"}),
        }
        
    def __init__(self, *args, **kwargs):
        shop = kwargs.pop("shop", None)
        super().__init__(*args, **kwargs)
        
        
        if shop:
            self.fields["category"].queryset = Category.objects.filter(shop=shop)
        # if shop:
        #     self.fields["category"].queryset = Category.objects.filter(shop=shop)
            
        #     self.fields["category"].label_from_instance = lambda cat: cat.name
        # self.fields['image'].widget.clear_checkbox_label = ''
        # self.fields['category'].empty_label = None
        
class ProductVariantForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ["image", "barcode", "sku", "price", "discount_percentage", "stock_quantity", "reorder_point", "product_attribute_values"]
        widgets = {
            "barcode": forms.TextInput(attrs={"class": "form-input"}),
            "sku": forms.TextInput(attrs={"class": "form-input"}),
            "price": forms.NumberInput(attrs={"class": "form-input"}),
            "discount_percentage": forms.NumberInput(attrs={"class": "form-input"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-input"}),
            "reorder_point": forms.NumberInput(attrs={"class": "form-input"}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for name, field in self.fields.items():
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} form-input {name}-input'
        
        
ProductVariantFormSet = inlineformset_factory(
    Product,
    ProductVariant,
    form=ProductVariantForm,
    extra=0,          # show 1 empty variant by default
    min_num=1,        # at least one variant
    validate_min=True,
    can_delete=False,
)