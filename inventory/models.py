# inventory/models.py (updated)
from django.db import models
from core.models import CustomField, DynamicFormData

class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color_code = models.CharField(max_length=7, default='#667eea', help_text='Hex color code for category')
    icon = models.CharField(max_length=50, blank=True, help_text='Font Awesome icon class')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
    ]
    
    STOCK_STATUS_CHOICES = [
        ('in_stock', 'In Stock'),
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=100, unique=True, help_text='Stock Keeping Unit')
    barcode = models.CharField(max_length=100, blank=True, help_text='Product barcode')
    description = models.TextField(blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, related_name='products')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    minimum_stock = models.PositiveIntegerField(default=10, help_text='Minimum stock level before alert')
    stock_status = models.CharField(max_length=15, choices=STOCK_STATUS_CHOICES, default='in_stock')
    unit_of_measure = models.CharField(max_length=20, default='pcs', help_text='e.g., pcs, kg, liters')
    
    # Additional fields that can be managed via custom fields
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    supplier = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(blank=True, null=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text='Weight in kg')
    dimensions = models.CharField(max_length=100, blank=True, help_text='LxWxH in cm')
    
    # Status and tracking
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def save(self, *args, **kwargs):
        # Update stock status based on quantity
        if self.stock_quantity == 0:
            self.stock_status = 'out_of_stock'
        elif self.stock_quantity <= self.minimum_stock:
            self.stock_status = 'low_stock'
        else:
            self.stock_status = 'in_stock'
        super().save(*args, **kwargs)

class ProductDynamicData(models.Model):
    """
    Store dynamic field data for products using the same structure as DynamicFormData
    """
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='dynamic_data')
    form_data = models.JSONField(default=dict, help_text="Dynamic form data for this product")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Dynamic data for {self.product.name}"

class InventoryTransaction(models.Model):
    """
    Track all inventory changes
    """
    TRANSACTION_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('sale', 'Sale'),
        ('return', 'Return'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=15, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=100, blank=True, help_text='Reference number')
    notes = models.TextField(blank=True)
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Inventory Transaction'
        verbose_name_plural = 'Inventory Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - {self.quantity} {self.product.name}"


class StockAdjustment(models.Model):
    """
    Track stock adjustments for audit trail
    """
    ADJUSTMENT_TYPES = [
        ('restock', 'Restock'),
        ('reduce', 'Reduce'),
        ('adjustment', 'Manual Adjustment'),
        ('damage', 'Damage/Loss'),
        ('return', 'Return to Stock'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_adjustments')
    adjustment_type = models.CharField(max_length=15, choices=ADJUSTMENT_TYPES)
    quantity = models.IntegerField(help_text="Quantity to add/remove")
    reason = models.TextField(blank=True, help_text="Reason for adjustment")
    reference_number = models.CharField(max_length=100, blank=True, help_text="Reference number")
    performed_by = models.CharField(max_length=100, help_text="User who performed adjustment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Stock Adjustment'
        verbose_name_plural = 'Stock Adjustments'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.adjustment_type} - {self.quantity} {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Update product stock based on adjustment
        if self.adjustment_type in ['restock', 'return']:
            self.product.stock_quantity += abs(self.quantity)
        elif self.adjustment_type in ['reduce', 'damage']:
            self.product.stock_quantity -= abs(self.quantity)
        
        # Ensure stock doesn't go negative
        if self.product.stock_quantity < 0:
            self.product.stock_quantity = 0
            
        # Update stock status
        self.product.save()
        super().save(*args, **kwargs)