from django import forms
from .models import ProductVariant, Category

class ProductForm(forms.ModelForm):
    class Meta:
        model = ProductVariant
        fields = ['image', 'name', 'barcode', 'price', 'discount_percentage', 'stock_quantity', 'reorder_point']

    def __init__(self, *args, **kwargs):
        shop = kwargs.pop("shop", None)
        super().__init__(*args, **kwargs)
        # if shop:
        #     self.fields["category"].queryset = Category.objects.filter(shop=shop)
            
        #     self.fields["category"].label_from_instance = lambda cat: cat.name
        self.fields['image'].widget.clear_checkbox_label = ''
        # self.fields['category'].empty_label = None