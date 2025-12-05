# accounts/views.py (corrected)
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import CustomLoginForm, UserRegistrationForm
from .decorators import role_required

def login_view(request):
    if request.method == 'POST':
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Redirect based on role
                if user.role == 'cashier':
                    return redirect('sales:pos')
                else:
                    return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = CustomLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')

# core/views.py (Updated dashboard function)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from inventory.models import Product
from accounts.models import CustomUser
from sales.models import POSOrder, POSOrderItem, DailySalesSummary



# accounts/views.py (Corrected dashboard function)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Count, Avg, F
from datetime import datetime, timedelta
from inventory.models import Product
from accounts.models import CustomUser
from sales.models import (
    POSOrder, 
    POSOrderItem, 
    DailySalesSummary, 
    UnusualTransaction
)
from django.db.models import Q

@login_required
def dashboard(request):
    """Main dashboard with real data"""
    today = timezone.now().date()
    current_week_start = today - timedelta(days=today.weekday())
    current_month_start = today.replace(day=1)
    yesterday = today - timedelta(days=1)

    # Get today's summary
    today_summary = DailySalesSummary.objects.filter(date=today).first()

    # Calculate today's metrics
    today_orders = POSOrder.objects.filter(
        created_at__date=today,
        status='completed'
    )

    today_sales = today_orders.aggregate(total=Sum('final_amount'))['total'] or 0
    today_transactions = today_orders.count()
    today_customers = today_orders.aggregate(
        count=Count('customer_name', distinct=True)
    )['count'] or 0

    # Calculate averages
    avg_order_value = today_orders.aggregate(avg=Avg('final_amount'))['avg'] or 0

    # Calculate weekly metrics
    weekly_orders = POSOrder.objects.filter(
        created_at__date__gte=current_week_start,
        created_at__date__lte=today,
        status='completed'
    )
    weekly_sales = weekly_orders.aggregate(total=Sum('final_amount'))['total'] or 0
    weekly_transactions = weekly_orders.count()

    # Calculate monthly metrics
    monthly_orders = POSOrder.objects.filter(
        created_at__date__gte=current_month_start,
        created_at__date__lte=today,
        status='completed'
    )
    monthly_sales = monthly_orders.aggregate(total=Sum('final_amount'))['total'] or 0
    monthly_transactions = monthly_orders.count()

    # Inventory metrics
    total_inventory = Product.objects.count()
    low_stock_products = Product.objects.filter(
        stock_status='low_stock'
    ).count()
    out_of_stock_products = Product.objects.filter(
        stock_status='out_of_stock'
    ).count()

    # User metrics
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()

    # Top selling items (today)
    top_selling_items = POSOrderItem.objects.filter(
        order__created_at__date=today,
        order__status='completed'
    ).values('product__name', 'product__sku').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_quantity')[:5]

    # Payment method breakdown
    payment_breakdown = POSOrder.objects.filter(
        created_at__date=today,
        status='completed'
    ).values('payment_method').annotate(
        total=Sum('final_amount'),
        count=Count('id')
    ).order_by('-total')

    # Recent orders
    recent_orders = POSOrder.objects.filter(
        created_at__date=today,
        status='completed'
    ).order_by('-created_at')[:5]

    # Best customers (today)
    best_customers = POSOrder.objects.filter(
        created_at__date=today,
        status='completed',
        customer_name__isnull=False
    ).values('customer_name').annotate(
        total_spent=Sum('final_amount'),
        orders=Count('id')
    ).order_by('-total_spent')[:5]

    # Unusual transactions
    unusual_transactions = UnusualTransaction.objects.filter(
        order__created_at__date=today
    ).select_related('order')[:5]

    # Sales trend (last 7 days)
    sales_trend = []
    for i in range(7):
        date = today - timedelta(days=i)
        day_sales = POSOrder.objects.filter(
            created_at__date=date,
            status='completed'
        ).aggregate(total=Sum('final_amount'))['total'] or 0
        sales_trend.append({
            'date': date.strftime('%a'),
            'sales': float(day_sales)
        })
    sales_trend.reverse()  # Most recent first

    # Product categories performance
    category_performance = POSOrderItem.objects.filter(
        order__created_at__date=today,
        order__status='completed'
    ).values('product__category__name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')[:5]

    # Cashier performance
    cashier_performance = POSOrder.objects.filter(
        created_at__date=today,
        status='completed'
    ).values('cashier').annotate(
        total_sales=Sum('final_amount'),
        total_orders=Count('id')
    ).order_by('-total_sales')

    # Calculate in-stock products
    in_stock_products = total_inventory - low_stock_products - out_of_stock_products

    # Yesterday's summary
    yesterday_summary = DailySalesSummary.objects.filter(date=yesterday).first()
    yesterday_sales = yesterday_summary.total_revenue if yesterday_summary else 0
    yesterday_transactions = yesterday_summary.total_transactions if yesterday_summary else 0

    # Sales growth percentage
    sales_growth_percentage = (
        ((today_sales - yesterday_sales) / yesterday_sales) * 100
        if yesterday_sales > 0 else 0
    )

    context = {
        # Sales metrics
        'today_sales': today_sales,
        'today_transactions': today_transactions,
        'today_customers': today_customers,
        'avg_order_value': avg_order_value,
        'in_stock_products': in_stock_products,

        'weekly_sales': weekly_sales,
        'weekly_transactions': weekly_transactions,
        'monthly_sales': monthly_sales,
        'monthly_transactions': monthly_transactions,

        # Inventory metrics
        'total_inventory': total_inventory,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,

        # User metrics
        'total_users': total_users,
        'active_users': active_users,

        # Top items
        'top_selling_items': top_selling_items,

        # Payment methods
        'payment_breakdown': payment_breakdown,

        # Recent data
        'recent_orders': recent_orders,
        'best_customers': best_customers,
        'unusual_transactions': unusual_transactions,

        # Trends
        'sales_trend': sales_trend,
        'category_performance': category_performance,
        'cashier_performance': cashier_performance,

        # Yesterday's data
        'yesterday_sales': yesterday_sales,
        'yesterday_transactions': yesterday_transactions,
        'sales_growth_percentage': sales_growth_percentage,

        # User info
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'accounts/dashboard.html', context)



# accounts/views.py (Updated with edit user functionality)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from .forms import UserRegistrationForm
from .models import CustomUser
from .decorators import role_required

@role_required(['admin', 'manager'])
def user_management(request):
    users = CustomUser.objects.all()
    context = {
        'users': users,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'accounts/user_management.html', context)

@role_required(['admin'])
def create_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User {user.username} created successfully!')
            return redirect('user_management')
    else:
        form = UserRegistrationForm()
    context = {
        'form': form,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'accounts/create_user.html', context)

@role_required(['admin'])
def edit_user(request, user_id):
    """Edit existing user"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        role = request.POST.get('role', 'cashier')
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        
        # Validate input
        if not username:
            messages.error(request, 'Username is required')
            return render(request, 'accounts/edit_user.html', {
                'user': user,
                'user_role': request.user.role,
                'user_name': request.user.get_full_name() or request.user.username,
            })
        
        # Check if username already exists (excluding current user)
        if CustomUser.objects.filter(username=username).exclude(id=user_id).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'accounts/edit_user.html', {
                'user': user,
                'user_role': request.user.role,
                'user_name': request.user.get_full_name() or request.user.username,
            })
        
        # Update user fields
        user.username = username
        user.email = email
        user.role = role
        user.phone = phone
        
        # Update password if provided
        if password:
            user.password = make_password(password)
        
        try:
            user.save()
            messages.success(request, f'User {user.username} updated successfully!')
            return redirect('user_management')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    else:
        # Pre-populate form with current user data
        context = {
            'user': user,
            'user_role': request.user.role,
            'user_name': request.user.get_full_name() or request.user.username,
        }
        return render(request, 'accounts/edit_user.html', context)

@role_required(['admin'])
def delete_user(request, user_id):
    """Delete user"""
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        username = user.username
        user.delete()
        messages.success(request, f'User {username} deleted successfully!')
        return redirect('user_management')
    
    return redirect('user_management')