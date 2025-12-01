# core/forms.py
from django import forms
from .models import SystemSettings, FieldCategory, CustomField


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = [
            'business_name', 'business_address', 'business_phone', 'business_email',
            'currency', 'logo', 'show_inventory', 'show_receipts', 'show_analytics',
            'show_reports', 'enable_sms', 'enable_email', 'primary_color',
            'secondary_color', 'accent_color', 'card_radius', 'receipt_header',
            'receipt_footer', 'show_receipt_logo', 'analytics_refresh_rate'
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Enter business name'}),
            'business_address': forms.Textarea(attrs={'class': 'form-control gradient-input', 'rows': 3, 'placeholder': 'Enter business address'}),
            'business_phone': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Enter phone number'}),
            'business_email': forms.EmailInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Enter email address'}),
            'currency': forms.Select(attrs={'class': 'form-control gradient-select'}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'receipt_header': forms.Textarea(attrs={'class': 'form-control gradient-input', 'rows': 2, 'placeholder': 'Receipt header text'}),
            'receipt_footer': forms.Textarea(attrs={'class': 'form-control gradient-input', 'rows': 2, 'placeholder': 'Receipt footer text'}),
            'primary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'secondary_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'accent_color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'card_radius': forms.NumberInput(attrs={'class': 'form-control gradient-input', 'min': '0', 'max': '50'}),
            'analytics_refresh_rate': forms.NumberInput(attrs={'class': 'form-control gradient-input', 'min': '10', 'max': '300'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add custom styling to boolean fields
        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs.update({'class': 'form-check-input'})



class FieldCategoryForm(forms.ModelForm):
    class Meta:
        model = FieldCategory
        fields = ['name', 'description', 'icon']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Category name'}),
            'description': forms.Textarea(attrs={'class': 'form-control gradient-input', 'rows': 2, 'placeholder': 'Description'}),
            'icon': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Font Awesome icon class (e.g., fa-box)'}),
        }

class CustomFieldForm(forms.ModelForm):
    class Meta:
        model = CustomField
        fields = [
            'category', 'name', 'field_type', 'label', 'placeholder', 'help_text',
            'required', 'show_on_receipt', 'show_on_reports', 'show_on_pos',
            'default_value', 'validation_rules', 'dropdown_options', 'order'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control gradient-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Internal field name'}),
            'field_type': forms.Select(attrs={'class': 'form-control gradient-select'}),
            'label': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Display label'}),
            'placeholder': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Placeholder text'}),
            'help_text': forms.Textarea(attrs={'class': 'form-control gradient-input', 'rows': 2, 'placeholder': 'Help text'}),
            'default_value': forms.TextInput(attrs={'class': 'form-control gradient-input', 'placeholder': 'Default value'}),
            'validation_rules': forms.Textarea(attrs={'class': 'form-control gradient-input', 'rows': 3, 'placeholder': 'Validation rules as JSON'}),
            'dropdown_options': forms.Textarea(attrs={'class': 'form-control gradient-input', 'rows': 3, 'placeholder': 'Dropdown options as JSON array'}),
            'order': forms.NumberInput(attrs={'class': 'form-control gradient-input', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.BooleanField):
                field.widget.attrs.update({'class': 'form-check-input'})

