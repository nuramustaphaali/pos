# sales/views.py (COMPLETE - Single working version)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
import json
from inventory.models import Product
from core.models import SystemSettings, CustomField, DynamicFormData
from .models import POSOrder, POSOrderItem, PaymentTransaction, SaleSummary, DailySalesSummary, UnusualTransaction
from .forms import POSOrderForm, POSOrderItemForm

# sales/views.py (FIXED - Corrected decimal/float operations)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
import json
from inventory.models import Product
from core.models import SystemSettings, CustomField, DynamicFormData
from .models import POSOrder, POSOrderItem, PaymentTransaction, SaleSummary, DailySalesSummary, UnusualTransaction
from .forms import POSOrderForm, POSOrderItemForm

@login_required
def pos_sales(request):
    """Main POS sales screen with product selection dropdown"""
    # Get system settings
    system_settings = SystemSettings.objects.first()
    
    # Get active products for selection dropdown
    products = Product.objects.filter(status='active').order_by('name').values(
        'id', 'name', 'sku', 'barcode', 'price', 'stock_quantity'
    )
    
    # Debug: Print products to terminal
    print(f"DEBUG: Found {len(products)} active products")
    for product in products:
        print(f"DEBUG: Product - Name: {product['name']}, SKU: {product['sku']}, Barcode: {product['barcode']}")
    
    # Create new order if not exists in session
    if 'current_order_id' not in request.session:
        order = POSOrder.objects.create(
            order_number=f"POS{timezone.now().strftime('%Y%m%d%H%M%S')}",
            total_amount=0,
            final_amount=0,
            cashier=request.user.username,
            payment_method='cash'
        )
        request.session['current_order_id'] = order.id
        print(f"DEBUG: Created new order {order.id}")
    else:
        order = get_object_or_404(POSOrder, id=request.session['current_order_id'])
        print(f"DEBUG: Using existing order {order.id}")
    
    # Get order items
    order_items = POSOrderItem.objects.filter(order=order).select_related('product')
    
    # Calculate totals - FIXED: Convert to float for multiplication
    subtotal = sum(float(item.total_price) for item in order_items)
    tax_amount = subtotal * 0.00  # 7.5% tax - FIXED: Use float
    final_total = subtotal + tax_amount
    
    # Update order with calculated totals
    order.total_amount = subtotal
    order.tax_amount = tax_amount
    order.final_amount = final_total
    order.save()
    
    # Handle form submission for adding items
    if request.method == 'POST':
        action = request.POST.get('action', '')
        print(f"DEBUG: Action received: {action}")
        
        if action == 'add_item':
            # Get the selected product from the form
            selected_sku = request.POST.get('selected_product', '').strip()
            quantity = int(request.POST.get('quantity', 1))
            
            print(f"DEBUG: Adding item - Selected SKU: '{selected_sku}', Quantity: {quantity}")
            
            # Find product by SKU (since we're using SKU as the value in the dropdown)
            product = Product.objects.filter(sku=selected_sku).first()
            
            if not product:
                messages.error(request, f'Product not found with SKU: {selected_sku}')
                print(f"DEBUG: Product not found with SKU: {selected_sku}")
            elif product.stock_quantity < quantity:
                messages.error(request, f'Insufficient stock for {product.name}. Available: {product.stock_quantity}')
                print(f"DEBUG: Insufficient stock for {product.name}. Available: {product.stock_quantity}")
            else:
                # Check if item already exists in order
                existing_item = POSOrderItem.objects.filter(
                    order=order, product=product
                ).first()
                
                if existing_item:
                    new_quantity = existing_item.quantity + quantity
                    if new_quantity > product.stock_quantity:
                        messages.error(request, f'Insufficient stock for {product.name}. Available: {product.stock_quantity}')
                        print(f"DEBUG: Insufficient stock after adding. Available: {product.stock_quantity}")
                    else:
                        existing_item.quantity = new_quantity
                        # FIXED: Convert to float for multiplication
                        existing_item.total_price = float(existing_item.unit_price) * new_quantity
                        existing_item.save()
                        # Update stock
                        product.stock_quantity -= quantity
                        product.save()
                        messages.success(request, f'Added {quantity} more {product.name} to cart')
                        print(f"DEBUG: Added {quantity} more {product.name} to cart (existing item)")
                else:
                    # Create new item - FIXED: Convert to float for multiplication
                    POSOrderItem.objects.create(
                        order=order,
                        product=product,
                        quantity=quantity,
                        unit_price=product.price,
                        total_price=float(product.price) * quantity
                    )
                    # Update stock
                    product.stock_quantity -= quantity
                    product.save()
                    messages.success(request, f'Added {quantity} {product.name} to cart')
                    print(f"DEBUG: Added {quantity} {product.name} to cart (new item)")
        
        elif action == 'remove_item':
            item_id = request.POST.get('item_id', '')
            print(f"DEBUG: Removing item with ID: {item_id}")
            try:
                order_item = get_object_or_404(POSOrderItem, id=item_id)
                # Restore stock
                order_item.product.stock_quantity += order_item.quantity
                order_item.product.save()
                # Delete item
                order_item.delete()
                messages.success(request, 'Item removed from cart')
                print(f"DEBUG: Item {item_id} removed from cart")
            except:
                messages.error(request, 'Error removing item')
                print(f"DEBUG: Error removing item {item_id}")
        
        elif action == 'clear_order':
            # Restore stock for all items
            for item in order.items.all():
                item.product.stock_quantity += item.quantity
                item.product.save()
                print(f"DEBUG: Restored {item.quantity} stock for {item.product.name}")
            # Delete order
            order.delete()
            # Clear session
            del request.session['current_order_id']
            messages.info(request, 'Current order cleared')
            print(f"DEBUG: Order cleared and session deleted")
            return redirect('sales:pos')
        
        elif action == 'complete_order':
            # Get payment method and reference from form
            payment_method = request.POST.get('payment_method', 'cash')
            reference_number = request.POST.get('reference_number', '')
            customer_name = request.POST.get('customer_name', '')
            customer_phone = request.POST.get('customer_phone', '')
            
            print(f"DEBUG: Completing order - Payment: {payment_method}, Customer: {customer_name}")
            
            # Update order
            order.payment_method = payment_method
            order.customer_name = customer_name
            order.customer_phone = customer_phone
            order.status = 'completed'
            order.save()
            
            # Clear session
            del request.session['current_order_id']
            
            messages.success(request, f'Order #{order.order_number} completed successfully!')
            print(f"DEBUG: Order {order.order_number} completed successfully!")
            return redirect('sales:print_receipt', order_id=order.id)
        
        # Refresh page to show updated cart
        return redirect('sales:pos')
    
    print(f"DEBUG: Rendering POS page with {order_items.count()} items in cart")
    context = {
        'order': order,
        'order_items': order_items,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'final_total': final_total,
        'products': products,
        'system_settings': system_settings,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'sales/pos_sales.html', context)


@login_required
def print_receipt(request, order_id):
    """Print receipt for completed order"""
    order = get_object_or_404(POSOrder, id=order_id)
    order_items = POSOrderItem.objects.filter(order=order).select_related('product')
    
    # Get system settings for receipt
    system_settings = SystemSettings.objects.first()
    
    context = {
        'order': order,
        'order_items': order_items,
        'system_settings': system_settings,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'sales/receipt.html', context)

@login_required
def repeat_sale(request, order_id):
    """Create a new order with same items as the original order"""
    original_order = get_object_or_404(POSOrder, id=order_id)
    
    # Create new order
    new_order = POSOrder.objects.create(
        order_number=f"POS{timezone.now().strftime('%Y%m%d%H%M%S')}",
        total_amount=0,
        final_amount=0,
        cashier=request.user.username,
        payment_method='cash'
    )
    
    # Copy items
    for item in original_order.items.all():
        # Check if product still exists and has sufficient stock
        if item.product.stock_quantity >= item.quantity:
            POSOrderItem.objects.create(
                order=new_order,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price
            )
            # Update stock
            item.product.stock_quantity -= item.quantity
            item.product.save()
        else:
            messages.warning(request, f'Insufficient stock for {item.product.name}')
    
    # Recalculate totals
    order_items = POSOrderItem.objects.filter(order=new_order)
    subtotal = sum(item.total_price for item in order_items)
    tax_amount = subtotal * 0.075
    final_total = subtotal + tax_amount
    
    new_order.total_amount = subtotal
    new_order.tax_amount = tax_amount
    new_order.final_amount = final_total
    new_order.save()
    
    # Set as current order
    request.session['current_order_id'] = new_order.id
    
    messages.success(request, 'Sale repeated successfully!')
    return redirect('sales:pos')

@login_required
def payment_summary(request):
    """View for payment summaries and analytics"""
    # Get today's summary
    today = timezone.now().date()
    today_summary = SaleSummary.objects.filter(date=today).first()
    
    # Get recent summaries
    recent_summaries = SaleSummary.objects.filter(
        date__gte=today - timedelta(days=7)
    ).order_by('-date')
    
    # Payment method distribution
    payment_methods = PaymentTransaction.objects.filter(
        created_at__date=today
    ).values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id')
    )
    
    context = {
        'today_summary': today_summary,
        'recent_summaries': recent_summaries,
        'payment_methods': payment_methods,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'sales/payment_summary.html', context)


# sales/views.py (FINAL - Complete working version)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
import csv
import json
from inventory.models import Product
from core.models import SystemSettings, CustomField, DynamicFormData
from .models import POSOrder, POSOrderItem, PaymentTransaction, SaleSummary, DailySalesSummary, UnusualTransaction
from .forms import POSOrderForm, POSOrderItemForm

@login_required
def daily_dashboard(request):
    """Today's sales dashboard"""
    today = timezone.now().date()
    
    # Get or create today's summary
    summary, created = DailySalesSummary.objects.get_or_create(
        date=today,
        defaults={
            'total_revenue': 0,
            'total_transactions': 0,
            'cash_revenue': 0,
            'cash_transactions': 0,
            'transfer_revenue': 0,
            'transfer_transactions': 0,
            'pos_revenue': 0,
            'pos_transactions': 0,
            'mobile_money_revenue': 0,
            'mobile_money_transactions': 0,
        }
    )
    
    # Always regenerate summary to get latest data
    orders = POSOrder.objects.filter(created_at__date=today, status='completed')
    
    summary.total_revenue = orders.aggregate(total=Sum('final_amount'))['total'] or 0
    summary.total_transactions = orders.count()
    
    # Calculate method-specific totals
    for method in ['cash', 'transfer', 'pos', 'mobile_money']:
        method_orders = orders.filter(payment_method=method)
        summary_data = method_orders.aggregate(total=Sum('final_amount'), count=Count('id'))
        setattr(summary, f'{method}_revenue', summary_data['total'] or 0)
        setattr(summary, f'{method}_transactions', summary_data['count'] or 0)
    
    summary.save()
    
    # Get low stock products
    low_stock_products = Product.objects.filter(
        stock_status__in=['low_stock', 'out_of_stock']
    )[:5]
    
    # Get today's orders for real-time updates
    today_orders = POSOrder.objects.filter(
        created_at__date=today,
        status='completed'
    ).order_by('-created_at')
    
    context = {
        'summary': summary,
        'low_stock_products': low_stock_products,
        'today_orders': today_orders,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'sales/daily_dashboard.html', context)

@login_required
def yesterday_summary(request):
    """Yesterday's sales summary"""
    yesterday = timezone.now().date() - timedelta(days=1)
    
    # Get or create yesterday's summary
    summary, created = DailySalesSummary.objects.get_or_create(
        date=yesterday,
        defaults={
            'total_revenue': 0,
            'total_transactions': 0,
            'cash_revenue': 0,
            'cash_transactions': 0,
            'transfer_revenue': 0,
            'transfer_transactions': 0,
            'pos_revenue': 0,
            'pos_transactions': 0,
            'mobile_money_revenue': 0,
            'mobile_money_transactions': 0,
        }
    )
    
    # Always regenerate summary to get latest data
    orders = POSOrder.objects.filter(created_at__date=yesterday, status='completed')
    
    summary.total_revenue = orders.aggregate(total=Sum('final_amount'))['total'] or 0
    summary.total_transactions = orders.count()
    
    # Calculate method-specific totals
    for method in ['cash', 'transfer', 'pos', 'mobile_money']:
        method_orders = orders.filter(payment_method=method)
        summary_data = method_orders.aggregate(total=Sum('final_amount'), count=Count('id'))
        setattr(summary, f'{method}_revenue', summary_data['total'] or 0)
        setattr(summary, f'{method}_transactions', summary_data['count'] or 0)
    
    summary.save()
    
    # Get yesterday's orders
    yesterday_orders = POSOrder.objects.filter(
        created_at__date=yesterday,
        status='completed'
    ).order_by('-created_at')
    
    # Get unusual transactions for yesterday
    unusual_transactions = UnusualTransaction.objects.filter(
        order__created_at__date=yesterday
    ).select_related('order')
    
    # Apply filters if any
    payment_method = request.GET.get('payment_method', '')
    min_amount = request.GET.get('min_amount', '')
    
    if payment_method:
        yesterday_orders = yesterday_orders.filter(payment_method=payment_method)
    
    if min_amount:
        try:
            min_amount_float = float(min_amount)
            yesterday_orders = yesterday_orders.filter(final_amount__gte=min_amount_float)
        except ValueError:
            # If conversion fails, ignore the filter
            pass
    
    # Export to CSV functionality
    if request.GET.get('export') == 'csv':
        return export_yesterday_orders_csv(yesterday_orders)
    
    context = {
        'summary': summary,
        'yesterday_orders': yesterday_orders,
        'unusual_transactions': unusual_transactions,
        'payment_method': payment_method,
        'min_amount': min_amount,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'sales/yesterday_summary.html', context)

def export_yesterday_orders_csv(orders):
    """Export yesterday's orders to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="yesterday_orders.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Date', 'Cashier', 'Payment Method', 
        'Total Amount', 'Customer Name', 'Customer Phone'
    ])
    
    for order in orders:
        writer.writerow([
            order.order_number,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.cashier,
            order.get_payment_method_display(),
            order.final_amount,
            order.customer_name,
            order.customer_phone
        ])
    
    return response
    


@login_required
def generate_receipt_with_qr(request, order_id):
    """Generate receipt with QR code for verification"""
    import qrcode
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from io import BytesIO
    
    order = get_object_or_404(POSOrder, id=order_id)
    order_items = POSOrderItem.objects.filter(order=order).select_related('product')
    
    # Get system settings
    system_settings = SystemSettings.objects.first()
    
    # Generate QR code for order verification
    qr_data = f"{request.build_absolute_uri('/sales/verify-order/')}?order={order.order_number}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_image = buffer.getvalue()
    
    # Create PDF receipt
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, system_settings.business_name or "Modern POS")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, system_settings.business_address or "")
    p.drawString(50, height - 85, f"Order: {order.order_number}")
    p.drawString(50, height - 100, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(50, height - 115, f"Cashier: {order.cashier}")
    
    # Items
    y_position = height - 150
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y_position, "Items")
    p.setFont("Helvetica", 10)
    
    y_position -= 20
    for item in order_items:
        p.drawString(50, y_position, f"{item.quantity} x {item.product.name}")
        p.drawString(300, y_position, f"₦{item.total_price}")
        y_position -= 15
    
    # Totals
    y_position -= 20
    p.line(50, y_position, 400, y_position)
    y_position -= 15
    p.drawString(50, y_position, f"Subtotal: ₦{order.total_amount}")
    y_position -= 15
    p.drawString(50, y_position, f"Tax: ₦{order.tax_amount}")
    y_position -= 15
    p.drawString(50, y_position, f"Total: ₦{order.final_amount}")
    y_position -= 15
    p.drawString(50, y_position, f"Payment: {order.get_payment_method_display()}")
    
    # QR Code
    if qr_image:
        p.drawString(50, y_position - 50, "Scan for order verification:")
        p.drawImage(BytesIO(qr_image), 50, y_position - 150, width=100, height=100)
    
    # Footer
    p.drawString(50, 50, system_settings.receipt_footer or "")
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='application/pdf')