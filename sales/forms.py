# sales/forms.py
from django import forms
from .models import POSOrder, POSOrderItem

class POSOrderForm(forms.ModelForm):
    class Meta:
        model = POSOrder
        fields = ['payment_method', 'customer_name', 'customer_phone']
        widgets = {
            'payment_method': forms.Select(attrs={'class': 'form-control gradient-select', 'id': 'paymentMethod'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Customer name (optional)'}),
            'customer_phone': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Customer phone (optional)'}),
        }

class POSOrderItemForm(forms.ModelForm):
    barcode = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control gradient-input',
            'placeholder': 'Scan barcode or enter SKU',
            'id': 'barcodeInput',
            'autofocus': True
        })
    )
    
    class Meta:
        model = POSOrderItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control gradient-input',
                'value': '1',
                'min': '1',
                'id': 'quantityInput'
            })
        }