# sales/models.py
from django.db import models
from inventory.models import Product
from core.models import SystemSettings

class POSOrder(models.Model):
    PAYMENT_METHODS = [
        ('pos', 'POS/ATM Card'),
        ('transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('credit', 'Credit'),
    ]
    
    ORDER_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order_number = models.CharField(max_length=50, unique=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=15, choices=ORDER_STATUS, default='pending')
    
    # Customer information
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    
    # Staff information
    cashier = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'POS Order'
        verbose_name_plural = 'POS Orders'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Order #{self.order_number}"

class POSOrderItem(models.Model):
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = 'POS Order Item'
        verbose_name_plural = 'POS Order Items'
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"

class POSReceiptSettings(models.Model):
    """
    Store receipt settings for POS orders
    """
    order = models.OneToOneField(POSOrder, on_delete=models.CASCADE, related_name='receipt_settings')
    show_product_details = models.BooleanField(default=True)
    show_customer_info = models.BooleanField(default=True)
    show_payment_info = models.BooleanField(default=True)
    custom_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Receipt settings for {self.order.order_number}"


# sales/models.py (add to existing models)
from django.db import models
from inventory.models import Product
from core.models import SystemSettings

class PaymentTransaction(models.Model):
    """
    Store payment transaction details
    """
    PAYMENT_METHODS = [
        ('pos', 'POS/ATM Card'),
        ('transfer', 'Bank Transfer'),
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('credit', 'Credit'),
        ('paystack', 'Paystack'),
        ('flutterwave', 'Flutterwave'),
    ]
    
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE, related_name='payments')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference_number = models.CharField(max_length=100, blank=True, help_text="Payment reference from gateway")
    transaction_id = models.CharField(max_length=100, blank=True, help_text="Gateway transaction ID")
    status = models.CharField(max_length=15, choices=TRANSACTION_STATUS, default='pending')
    gateway_response = models.JSONField(default=dict, blank=True, help_text="Full gateway response")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Payment Transaction'
        verbose_name_plural = 'Payment Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment_method} - ₦{self.amount} - {self.status}"

class SaleSummary(models.Model):
    """
    Daily sales summary for analytics
    """
    date = models.DateField()
    total_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    cash_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transfer_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pos_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mobile_money_sales = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_transactions = models.PositiveIntegerField(default=0)
    transfer_transactions = models.PositiveIntegerField(default=0)
    pos_transactions = models.PositiveIntegerField(default=0)
    mobile_money_transactions = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['date']
        verbose_name = 'Sale Summary'
        verbose_name_plural = 'Sale Summaries'
        ordering = ['-date']
    
    def __str__(self):
        return f"Summary for {self.date}"
    
    @classmethod
    def generate_summary(cls, date):
        """Generate daily sales summary"""
        from django.db.models import Sum, Count, Q
        
        orders = POSOrder.objects.filter(
            created_at__date=date,
            status='completed'
        )
        
        summary_data = {
            'date': date,
            'total_sales': orders.aggregate(total=Sum('final_amount'))['total'] or 0,
            'total_transactions': orders.count(),
        }
        
        # Calculate method-specific totals
        for method in ['cash', 'transfer', 'pos', 'mobile_money']:
            method_orders = orders.filter(payment_method=method)
            summary_data[f'{method}_sales'] = method_orders.aggregate(
                total=Sum('final_amount')
            )['total'] or 0
            summary_data[f'{method}_transactions'] = method_orders.count()
        
        summary, created = cls.objects.update_or_create(
            date=date,
            defaults=summary_data
        )
        return summary


# sales/models.py (add to existing models)
from django.db import models
from inventory.models import Product
from core.models import SystemSettings

class DailySalesSummary(models.Model):
    """
    Daily sales summary with detailed breakdown
    """
    date = models.DateField(unique=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_transactions = models.PositiveIntegerField(default=0)
    
    # Payment method breakdown
    cash_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    cash_transactions = models.PositiveIntegerField(default=0)
    
    transfer_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    transfer_transactions = models.PositiveIntegerField(default=0)
    
    pos_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pos_transactions = models.PositiveIntegerField(default=0)
    
    mobile_money_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mobile_money_transactions = models.PositiveIntegerField(default=0)
    
    # Top selling items (stored as JSON)
    top_selling_items = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Daily Sales Summary'
        verbose_name_plural = 'Daily Sales Summaries'
        ordering = ['-date']
    
    def __str__(self):
        return f"Sales Summary for {self.date}"
    
    @classmethod
    def generate_summary(cls, date):
        """Generate daily sales summary for a specific date"""
        from django.db.models import Sum, Count, Q
        from .models import POSOrder, POSOrderItem
        
        # Get orders for the specific date
        orders = POSOrder.objects.filter(
            created_at__date=date,
            status='completed'
        )
        
        summary_data = {
            'date': date,
            'total_revenue': orders.aggregate(total=Sum('final_amount'))['total'] or 0,
            'total_transactions': orders.count(),
        }
        
        # Calculate method-specific totals
        for method in ['pos', 'transfer', 'cash', 'mobile_money']:
            method_orders = orders.filter(payment_method=method)
            summary_data[f'{method}_revenue'] = method_orders.aggregate(
                total=Sum('final_amount')
            )['total'] or 0
            summary_data[f'{method}_transactions'] = method_orders.count()
        
        # Get top selling items
        order_items = POSOrderItem.objects.filter(
            order__created_at__date=date,
            order__status='completed'
        ).values('product__name', 'product__sku').annotate(
            total_quantity=Sum('quantity'),
            total_revenue=Sum('total_price')
        ).order_by('-total_quantity')[:5]
        
        top_items = []
        for item in order_items:
            top_items.append({
                'name': item['product__name'],
                'sku': item['product__sku'],
                'quantity': item['total_quantity'],
                'revenue': float(item['total_revenue'] or 0)
            })
        
        summary_data['top_selling_items'] = top_items
        
        summary, created = cls.objects.update_or_create(
            date=date,
            defaults=summary_data
        )
        return summary

class UnusualTransaction(models.Model):
    """
    Track unusual transactions for highlighting
    """
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE)
    reason = models.CharField(max_length=200, help_text="Reason for marking as unusual")
    flagged_by = models.CharField(max_length=100)
    flagged_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    resolved_by = models.CharField(max_length=100, blank=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Unusual Transaction'
        verbose_name_plural = 'Unusual Transactions'
        ordering = ['-flagged_at']
    
    def __str__(self):
        return f"Unusual: {self.order.order_number} - {self.reason}"



# sales/models.py (add to existing models)
from django.db import models
from inventory.models import Product
from accounts.models import CustomUser
from django.utils import timezone

class BulkImportLog(models.Model):
    """
    Log for bulk import operations
    """
    IMPORT_TYPES = [
        ('products', 'Products'),
        ('customers', 'Customers'),
        ('orders', 'Orders'),
    ]
    
    import_type = models.CharField(max_length=20, choices=IMPORT_TYPES)
    file_name = models.CharField(max_length=200)
    total_records = models.PositiveIntegerField()
    successful_records = models.PositiveIntegerField(default=0)
    failed_records = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, default='processing')
    error_log = models.TextField(blank=True, help_text="JSON formatted error log")
    imported_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Bulk Import Log'
        verbose_name_plural = 'Bulk Import Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.import_type} - {self.file_name}"

class DailyLimitSettings(models.Model):
    """
    Settings for daily limits
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    daily_order_limit = models.PositiveIntegerField(default=50, help_text="Maximum orders per day")
    daily_sales_limit = models.DecimalField(max_digits=12, decimal_places=2, default=50000, help_text="Maximum sales amount per day")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Daily Limit Setting'
        verbose_name_plural = 'Daily Limit Settings'
    
    def __str__(self):
        return f"Limits for {self.user.username}"

class DailyOrderCount(models.Model):
    """
    Track daily order counts for limit enforcement
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    date = models.DateField()
    order_count = models.PositiveIntegerField(default=0)
    sales_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['user', 'date']
        verbose_name = 'Daily Order Count'
        verbose_name_plural = 'Daily Order Counts'
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    @classmethod
    def increment_count(cls, user, order_amount):
        """Increment daily count for user"""
        today = timezone.now().date()
        counter, created = cls.objects.get_or_create(
            user=user,
            date=today,
            defaults={'order_count': 0, 'sales_amount': 0}
        )
        
        counter.order_count += 1
        counter.sales_amount += order_amount
        counter.save()
        return counter

class TransactionHistory(models.Model):
    """
    Detailed transaction history for reporting
    """
    date = models.DateField()
    order = models.ForeignKey(POSOrder, on_delete=models.CASCADE)
    cashier = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    customer_name = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Transaction History'
        verbose_name_plural = 'Transaction Histories'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['cashier']),
            models.Index(fields=['payment_method']),
        ]
    
    def __str__(self):
        return f"Transaction {self.order.order_number} - {self.date}"
    
    @classmethod
    def create_from_order(cls, order):
        """Create transaction history from POS order"""
        return cls.objects.create(
            date=order.created_at.date(),
            order=order,
            cashier=order.cashier,
            payment_method=order.payment_method,
            total_amount=order.final_amount,
            customer_name=order.customer_name,
            customer_phone=order.customer_phone
        )