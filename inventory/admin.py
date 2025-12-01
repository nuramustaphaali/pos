# inventory/admin.py (updated)
from django.contrib import admin
from .models import ProductCategory, Product, ProductDynamicData, InventoryTransaction

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'color_code', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'price', 'stock_quantity', 'stock_status', 'status', 'created_at')
    list_filter = ('category', 'status', 'stock_status', 'created_at')
    search_fields = ('name', 'sku', 'barcode')
    readonly_fields = ('stock_status',)

@admin.register(ProductDynamicData)
class ProductDynamicDataAdmin(admin.ModelAdmin):
    list_display = ('product', 'created_at')
    search_fields = ('product__name', 'product__sku')

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'quantity', 'reference', 'created_by', 'created_at')
    list_filter = ('transaction_type', 'created_at', 'product__category')
    search_fields = ('product__name', 'reference', 'notes')