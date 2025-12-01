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
]