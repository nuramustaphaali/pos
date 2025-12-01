# inventory/forms.py (complete updated form)
from django import forms
from .models import Product, ProductCategory, ProductDynamicData
from core.utils import DynamicFormEngine

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'color_code', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control gradient-input', 'rows': 3, 'placeholder': 'Description'}),
            'color_code': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'icon': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Font Awesome icon class'}),
        }

class ProductForm(forms.ModelForm):
    UNIT_OF_MEASURE_CHOICES = [
        ('pcs', 'Pieces'),
        ('kg', 'Kilograms'),
        ('g', 'Grams'),
        ('l', 'Liters'),
        ('ml', 'Milliliters'),
        ('m', 'Meters'),
        ('cm', 'Centimeters'),
        ('box', 'Box'),
        ('pack', 'Pack'),
        ('carton', 'Carton'),
        ('dozen', 'Dozen'),
        ('pair', 'Pair'),
        ('set', 'Set'),
        ('unit', 'Unit'),
        ('bundle', 'Bundle'),
        ('roll', 'Roll'),
        ('sheet', 'Sheet'),
        ('tablet', 'Tablet'),
        ('capsule', 'Capsule'),
        ('bottle', 'Bottle'),
    ]
    
    unit_of_measure = forms.ChoiceField(
        choices=UNIT_OF_MEASURE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control gradient-select'})
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'barcode', 'description', 'category', 'price', 'cost_price',
            'stock_quantity', 'minimum_stock', 'unit_of_measure', 'image', 'supplier',
            'expiry_date', 'weight', 'dimensions', 'status'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Product name'}),
            'sku': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'SKU/Code'}),
            'barcode': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Barcode (optional)'}),
            'description': forms.Textarea(attrs={'class': 'form-control gradient-input', 'rows': 3, 'placeholder': 'Description'}),
            'category': forms.Select(attrs={'class': 'form-control gradient-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control gradient-input', 'step': '0.01', 'placeholder': 'Selling price'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control gradient-input', 'step': '0.01', 'placeholder': 'Cost price'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Current stock'}),
            'minimum_stock': forms.NumberInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Min stock level'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'supplier': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Supplier name'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control gradient-input'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control gradient-input', 'step': '0.01', 'placeholder': 'Weight in kg'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'LxWxH in cm'}),
            'status': forms.Select(attrs={'class': 'form-control gradient-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the choices for unit_of_measure field
        self.fields['unit_of_measure'].choices = self.UNIT_OF_MEASURE_CHOICES
        # Set default value
        self.fields['unit_of_measure'].initial = 'pcs'

class DynamicProductForm(forms.Form):
    """
    Dynamic form for product-specific custom fields
    """
    def __init__(self, *args, **kwargs):
        product_category = kwargs.pop('product_category', None)
        super().__init__(*args, **kwargs)
        
        if product_category:
            # Add dynamic fields based on category
            # This would be implemented based on your custom field system
            pass