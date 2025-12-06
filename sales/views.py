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
import qrcode
import base64
from io import BytesIO
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
from django.core.exceptions import PermissionDenied
from core.utils import check_limit_or_block


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
            payment_method='pos'
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
            # Enforce daily order limit
            try:
                check_limit_or_block("orders_per_day")
            except PermissionDenied as e:
                messages.error(request, str(e))
                return redirect('sales:pos')

            # Get payment method and reference from form
            payment_method = request.POST.get('payment_method', 'pos')
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


from core.models import SystemSettings, CustomField, DynamicFormData
from .models import POSOrder, POSOrderItem, PaymentTransaction, SaleSummary, DailySalesSummary, UnusualTransaction


import string  # if not already at the top

BASE36_ALPHABET = string.digits + string.ascii_lowercase


def _to_base36(num: int) -> str:
    """Convert positive int to base36 (same as JS toString(36))."""
    if num == 0:
        return "0"
    result = ""
    while num > 0:
        num, rem = divmod(num, 36)
        result = BASE36_ALPHABET[rem] + result
    return result


def generate_verification_code(order: POSOrder, system_settings: SystemSettings = None) -> str:
    """
    Generate the same verification code as the JS on the receipt template.
    Raw string: order_number | created_at(YmdHis) | business_name
    Hash: 32-bit int, multiplied by 31 each step, base36, padded to 8, SP-XXXX-XXXX.
    """
    if system_settings is None:
        system_settings = SystemSettings.objects.first()

    business_name = system_settings.business_name if system_settings else ""
    created_str = order.created_at.strftime("%Y%m%d%H%M%S")

    raw = f"{order.order_number}|{created_str}|{business_name}"

    # Same hashing approach as JS
    h = 0
    for ch in raw:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF  # 32-bit

    code = _to_base36(h).upper()
    code = code.rjust(8, "0")[-8:]  # pad to 8, keep last 8
    return f"SP-{code[:4]}-{code[4:]}"
    
    
    

from django.utils import timezone  # already imported earlier in your file

def verify_order(request):
    """
    Public verification page for QR scans.
    URL: /sales/verify-order/?order=<order_number>
    """
    order_number = request.GET.get("order", "").strip()
    system_settings = SystemSettings.objects.first()

    order = None
    verification_code = None
    is_valid = False

    if order_number:
        order = POSOrder.objects.filter(order_number=order_number).first()
        if order:
            verification_code = generate_verification_code(order, system_settings)
            is_valid = True

    context = {
        "order_number": order_number,
        "order": order,
        "verification_code": verification_code,
        "is_valid": is_valid,
        "system_settings": system_settings,
    }
    return render(request, "sales/verify_order.html", context)




@login_required
def print_receipt(request, order_id):
    """Print HTML receipt (with QR) for completed order"""
    order = get_object_or_404(POSOrder, id=order_id)
    order_items = POSOrderItem.objects.filter(order=order).select_related('product')

    # Get system settings for receipt
    system_settings = SystemSettings.objects.first()

    # --- Generate QR code for HTML receipt ---
    qr_code_b64 = None
    try:
        # If you have a real verify view, better: reverse('sales:verify_order') + querystring
        qr_data = request.build_absolute_uri(
            f"/sales/verify-order/?order={order.order_number}"
        )

        qr = qrcode.QRCode(
            version=1,
            box_size=4,   # smaller boxes so it fits nicely in the 90x90px area
            border=1,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
    except Exception as e:
        # Optional: log instead of print in production
        print("QR generation error:", e)

    context = {
        'order': order,
        'order_items': order_items,
        'system_settings': system_settings,
        'qr_code': qr_code_b64,  # 👈 now template can use this
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

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum, Count
from .models import POSOrder, SaleSummary

@login_required
def payment_summary(request):
    """
    Payment summary view for displaying analytics and sales data.
    This function dynamically generates summaries for today and the last 7 days.
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Sum, Count

    # Get today's date
    today = timezone.now().date()

    # Generate today's summary
    today_orders = POSOrder.objects.filter(created_at__date=today, status='completed')
    today_summary_data = {
        'date': today,
        'total_sales': today_orders.aggregate(total=Sum('final_amount'))['total'] or 0,
        'total_transactions': today_orders.count(),
    }

    # Calculate method-specific totals for today
    for method in ['pos', 'transfer', 'cash', 'mobile_money']:
        method_orders = today_orders.filter(payment_method=method)
        today_summary_data[f'{method}_sales'] = method_orders.aggregate(
            total=Sum('final_amount')
        )['total'] or 0
        today_summary_data[f'{method}_transactions'] = method_orders.count()

    # Save or update today's summary in the database
    today_summary, created = SaleSummary.objects.update_or_create(
        date=today,
        defaults=today_summary_data
    )

    # Generate summaries for the last 7 days
    recent_dates = [today - timedelta(days=i) for i in range(7)]
    recent_summaries = []
    for date in recent_dates:
        orders = POSOrder.objects.filter(created_at__date=date, status='completed')
        summary_data = {
            'date': date,
            'total_sales': orders.aggregate(total=Sum('final_amount'))['total'] or 0,
            'total_transactions': orders.count(),
        }

        # Calculate method-specific totals for each day
        for method in ['pos', 'transfer', 'cash', 'mobile_money']:
            method_orders = orders.filter(payment_method=method)
            summary_data[f'{method}_sales'] = method_orders.aggregate(
                total=Sum('final_amount')
            )['total'] or 0
            summary_data[f'{method}_transactions'] = method_orders.count()

        # Save or update the summary in the database
        summary, _ = SaleSummary.objects.update_or_create(
            date=date,
            defaults=summary_data
        )
        recent_summaries.append(summary)

    # Fetch recent summaries (last 7 days) for display
    recent_summaries = SaleSummary.objects.filter(
        date__gte=today - timedelta(days=7)
    ).order_by('-date')

    # Calculate payment method distribution for today
    payment_methods = POSOrder.objects.filter(
        created_at__date=today,
        status='completed'
    ).values('payment_method').annotate(
        total=Sum('final_amount'),
        count=Count('id')
    ).order_by('-total')

    # Calculate percentages for payment methods
    total_amount = sum(pm['total'] or 0 for pm in payment_methods)
    for pm in payment_methods:
        pm['percentage'] = round(((pm['total'] or 0) / total_amount) * 100, 2) if total_amount > 0 else 0

    # Map payment method codes to human-readable names
    PAYMENT_METHOD_CHOICES = dict(POSOrder.PAYMENT_METHODS)
    for pm in payment_methods:
        pm['display_name'] = PAYMENT_METHOD_CHOICES.get(pm['payment_method'], "Unknown")

    # Context dictionary with detailed explanation of each variable
    context = {
        'summary': today_summary,  # Today's summary
        'today_summary': today_summary,  # Duplicate for template consistency
        'recent_summaries': recent_summaries,  # Last 7 days' summaries
        'payment_methods': payment_methods,  # Payment method distribution
        'user_role': request.user.role,  # User role (e.g., admin, cashier)
        'user_name': request.user.get_full_name() or request.user.username,  # User name
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

# sales/views.py (Updated daily_dashboard function)
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
    for method in ['pos', 'transfer', 'cash', 'mobile_money']:
        method_orders = orders.filter(payment_method=method)
        summary_data = method_orders.aggregate(total=Sum('final_amount'), count=Count('id'))
        setattr(summary, f'{method}_revenue', summary_data['total'] or 0)
        setattr(summary, f'{method}_transactions', summary_data['count'] or 0)
    
    summary.save()
    
    # Get top selling items for today
    top_selling_items = POSOrderItem.objects.filter(
        order__created_at__date=today,
        order__status='completed'
    ).values('product__name', 'product__sku').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:5]
    
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
        'top_selling_items': top_selling_items,
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
    for method in ['pos', 'transfer', 'cash', 'mobile_money']:
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
    from reportlab.lib.colors import Color
    from io import BytesIO

    order = get_object_or_404(POSOrder, id=order_id)
    order_items = POSOrderItem.objects.filter(order=order).select_related('product')

    # Get system settings
    system_settings = SystemSettings.objects.first()

    # Generate QR code
    qr_data = f"{request.build_absolute_uri('/sales/verify-order/')}?order={order.order_number}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_image = buffer.getvalue()

    # Create PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # -------------------------
    # BACKGROUND TEXTURE
    # -------------------------
    p.saveState()

    texture_color = Color(0.85, 0.85, 0.85, alpha=0.15)  # VERY light grey
    p.setFillColor(texture_color)
    p.setFont("Helvetica", 22)

    # Repeat the order number diagonally across the page
    for y in range(0, int(height), 120):
        for x in range(0, int(width), 250):
            p.drawString(x, y, str(order.order_number))

    p.restoreState()

    # -------------------------
    # HEADER (More Nigerian POS Style)
    # -------------------------
    p.setFont("Helvetica-Bold", 20)
    p.drawString(40, height - 60, system_settings.business_name or "MODERN POS")

    p.setFont("Helvetica", 11)
    p.drawString(40, height - 82, system_settings.business_address or "")

    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, height - 110, f"ORDER RECEIPT - #{order.order_number}")

    p.setFont("Helvetica", 10)
    p.drawString(40, height - 130, f"Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
    p.drawString(250, height - 130, f"Cashier: {order.cashier}")

    # -------------------------
    # ITEMS SECTION
    # -------------------------
    p.setFont("Helvetica-Bold", 12)
    y_position = height - 170
    p.drawString(40, y_position, "ITEMS PURCHASED")

    p.setFont("Helvetica", 10)
    y_position -= 20

    for item in order_items:
        p.drawString(40, y_position, f"{item.quantity} x {item.product.name}")
        p.drawRightString(400, y_position, f"₦{item.total_price}")
        y_position -= 16

    # -------------------------
    # TOTALS
    # -------------------------
    y_position -= 10
    p.line(40, y_position, 400, y_position)
    y_position -= 20

    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y_position, f"Subtotal:")
    p.drawRightString(400, y_position, f"₦{order.total_amount}")

    y_position -= 18
    p.drawString(40, y_position, "Tax:")
    p.drawRightString(400, y_position, f"₦{order.tax_amount}")

    y_position -= 18
    p.drawString(40, y_position, "Total Amount:")
    p.drawRightString(400, y_position, f"₦{order.final_amount}")

    y_position -= 18
    p.drawString(40, y_position, f"Payment Method:")
    p.drawRightString(400, y_position, order.get_payment_method_display())

    # -------------------------
    # QR CODE
    # -------------------------
    if qr_image:
        p.setFont("Helvetica", 10)
        p.drawString(40, y_position - 40, "Scan to verify order:")
        p.drawImage(BytesIO(qr_image), 40, y_position - 140, width=110, height=110)

    # -------------------------
    # FOOTER
    # -------------------------
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(40, 40, system_settings.receipt_footer or "Thank you for your patronage!")

    p.showPage()
    p.save()

    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='application/pdf')