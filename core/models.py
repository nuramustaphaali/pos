# core/models.py
from django.db import models

class SystemSettings(models.Model):
    BUSINESS_CURRENCIES = [
        ('NGN', 'Naira (₦)'),
        ('USD', 'Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'Pound (£)'),
    ]
    
    business_name = models.CharField(max_length=200, default='Modern POS Business')
    business_address = models.TextField(blank=True)
    business_phone = models.CharField(max_length=20, blank=True)
    business_email = models.EmailField(blank=True)
    currency = models.CharField(max_length=3, choices=BUSINESS_CURRENCIES, default='NGN')
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    
    # Toggle options
    show_inventory = models.BooleanField(default=True)
    show_receipts = models.BooleanField(default=True)
    show_analytics = models.BooleanField(default=True)
    show_reports = models.BooleanField(default=True)
    enable_sms = models.BooleanField(default=False)
    enable_email = models.BooleanField(default=False)
    
    # Theme settings
    primary_color = models.CharField(max_length=7, default='#667eea', help_text='Hex color code')
    secondary_color = models.CharField(max_length=7, default='#764ba2', help_text='Hex color code')
    accent_color = models.CharField(max_length=7, default='#f093fb', help_text='Hex color code')
    
    # Card styling
    card_radius = models.IntegerField(default=20, help_text='Border radius in pixels')
    card_shadow = models.CharField(max_length=50, default='0 10px 30px rgba(0, 0, 0, 0.1)', help_text='CSS shadow value')
    
    # Receipt settings
    receipt_header = models.TextField(blank=True, help_text='Text to appear at top of receipts')
    receipt_footer = models.TextField(blank=True, help_text='Text to appear at bottom of receipts')
    show_receipt_logo = models.BooleanField(default=True)
    
    # Analytics settings
    analytics_refresh_rate = models.IntegerField(default=30, help_text='Refresh rate in seconds')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'System Setting'
        verbose_name_plural = 'System Settings'
    
    def __str__(self):
        return f"{self.business_name} Settings"


class FieldCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Field Category'
        verbose_name_plural = 'Field Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class CustomField(models.Model):
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
        ('boolean', 'Yes/No'),
        ('dropdown', 'Dropdown'),
        ('textarea', 'Text Area'),
        ('image', 'Image Upload'),
        ('file', 'File Upload'),
        ('currency', 'Currency'),
        ('percentage', 'Percentage'),
    ]
    
    category = models.ForeignKey(FieldCategory, on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    label = models.CharField(max_length=200, help_text="Display label for the field")
    placeholder = models.CharField(max_length=200, blank=True, help_text="Placeholder text")
    help_text = models.TextField(blank=True, help_text="Help text to display")
    required = models.BooleanField(default=False)
    show_on_receipt = models.BooleanField(default=False)
    show_on_reports = models.BooleanField(default=False)
    show_on_pos = models.BooleanField(default=True)
    default_value = models.TextField(blank=True, help_text="Default value for the field")
    validation_rules = models.JSONField(default=dict, blank=True, help_text="Validation rules as JSON")
    order = models.PositiveIntegerField(default=0, help_text="Order in which field appears")
    
    # For dropdown fields
    dropdown_options = models.JSONField(default=list, blank=True, help_text="Dropdown options as JSON array")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Custom Field'
        verbose_name_plural = 'Custom Fields'
        ordering = ['category', 'order', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"
    
    @property
    def is_dropdown(self):
        return self.field_type == 'dropdown'
    
    @property
    def is_required(self):
        return self.required

class FieldValue(models.Model):
    """
    Stores the actual values for custom fields for specific records
    """
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=50, help_text="Model name (e.g., 'Product', 'Customer')")
    object_id = models.PositiveIntegerField(help_text="ID of the related object")
    value = models.TextField(help_text="The actual value stored")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['field', 'content_type', 'object_id']
        verbose_name = 'Field Value'
        verbose_name_plural = 'Field Values'
    
    def __str__(self):
        return f"{self.field.label}: {self.value}"


class DynamicFormData(models.Model):
    """
    Stores the complete form data for any content type
    """
    content_type = models.CharField(max_length=50, help_text="Model name (e.g., 'Product', 'Customer', 'Sale')")
    object_id = models.PositiveIntegerField(help_text="ID of the related object")
    form_data = models.JSONField(default=dict, help_text="Complete form data as JSON")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['content_type', 'object_id']
        verbose_name = 'Dynamic Form Data'
        verbose_name_plural = 'Dynamic Form Data'
    
    def __str__(self):
        return f"{self.content_type} - {self.object_id}"

class FormDataEntry(models.Model):
    """
    Individual form data entry for better querying and reporting
    """
    content_type = models.CharField(max_length=50)
    object_id = models.PositiveIntegerField()
    field_name = models.CharField(max_length=100)
    field_value = models.TextField()
    field_type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['content_type', 'object_id', 'field_name']
        verbose_name = 'Form Data Entry'
        verbose_name_plural = 'Form Data Entries'
    
    def __str__(self):
        return f"{self.content_type}.{self.field_name} = {self.field_value}"