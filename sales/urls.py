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
    path("verify-order/", views.verify_order, name="verify_order"),
]