# inventory/urls.py (add to existing urls)
from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='dashboard'),
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/edit/', views.edit_product, name='edit_product'),
    path('products/<int:product_id>/adjust-stock/', views.adjust_stock, name='adjust_stock'),
    path('products/<int:product_id>/restock/', views.restock_product, name='restock_product'),
    path('products/<int:product_id>/reduce-stock/', views.reduce_stock, name='reduce_stock'),
    path('categories/', views.product_category_list, name='category_list'),
    path('categories/add/', views.add_category, name='add_category'),
    path('stock-history/', views.stock_adjustment_history, name='stock_adjustment_history'),

    path('products/import/', views.product_bulk_import, name='product_bulk_import'),
    path('products/import/template/', views.product_import_template, name='product_import_template'),
    path('export/', views.export_center, name='export_center'),
    path('export/products/', views.product_bulk_export, name='product_bulk_export'),
    path('export/categories/', views.category_bulk_export, name='category_bulk_export'),
    path('export/stock-movements/', views.inventory_transactions_export, name='inventory_transactions_export'),
    path('export/stock-adjustments/', views.stock_adjustments_export, name='stock_adjustments_export'),

]