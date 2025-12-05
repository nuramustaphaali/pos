# sales/urls.py (COMPLETE)
from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('pos/', views.pos_sales, name='pos'),
    path('receipt/<int:order_id>/', views.print_receipt, name='print_receipt'),
    path('receipt/<int:order_id>/qr/', views.generate_receipt_with_qr, name='receipt_with_qr'),
    path('repeat/<int:order_id>/', views.repeat_sale, name='repeat_sale'),
    path('payment-summary/', views.payment_summary, name='payment_summary'),
    path('dashboard/', views.daily_dashboard, name='daily_dashboard'),
    path('yesterday/', views.yesterday_summary, name='yesterday_summary'),
    path('bulk-import/', views.bulk_import, name='bulk_import'),
    path('bulk-export/', views.bulk_export, name='bulk_export'),
    path('transaction-history/', views.transaction_history, name='transaction_history'),
    path('transaction/<int:order_id>/receipt/', views.print_transaction_receipt, name='print_transaction_receipt'),
    path('daily-limits/', views.daily_limits, name='daily_limits'),
]