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

@login_required
def dashboard(request):
    """Main dashboard with real data"""
    today = timezone.now().date()
    
    # Get today's summary
    today_summary = DailySalesSummary.objects.filter(date=today).first()
    
    # Calculate today's sales if summary doesn't exist
    if not today_summary:
        today_orders = POSOrder.objects.filter(
            created_at__date=today,
            status='completed'
        )
        today_sales = today_orders.aggregate(total=Sum('final_amount'))['total'] or 0
        today_transactions = today_orders.count()
    else:
        today_sales = today_summary.total_revenue
        today_transactions = today_summary.total_transactions
    
    # Get inventory data
    total_inventory = Product.objects.count()
    low_stock_products = Product.objects.filter(stock_status__in=['low_stock', 'out_of_stock']).count()
    
    # Get user data
    total_users = CustomUser.objects.count()
    active_users = CustomUser.objects.filter(is_active=True).count()
    
    # Get recent orders for timeline
    recent_orders = POSOrder.objects.filter(
        created_at__date=today,
        status='completed'
    ).order_by('-created_at')[:3]
    
    # Get recent inventory updates
    from inventory.models import InventoryTransaction
    recent_inventory_updates = InventoryTransaction.objects.filter(
        created_at__date=today
    ).order_by('-created_at')[:3]
    
    # Get recent user additions
    recent_users = CustomUser.objects.filter(
        date_joined__date=today
    ).order_by('-date_joined')[:3]
    
    # Combine timeline activities
    timeline_activities = []
    
    # Add recent orders
    for order in recent_orders:
        timeline_activities.append({
            'type': 'sale',
            'title': f'POS Sale #{order.order_number}',
            'amount': order.final_amount,
            'time': order.created_at.strftime('%H:%M'),
            'icon': 'fas fa-cash-register',
            'color': 'primary'
        })
    
    # Add recent inventory updates
    for update in recent_inventory_updates:
        timeline_activities.append({
            'type': 'inventory',
            'title': f'Inventory {update.transaction_type.title()}',
            'product': update.product.name,
            'quantity': update.quantity,
            'time': update.created_at.strftime('%H:%M'),
            'icon': 'fas fa-box',
            'color': 'success'
        })
    
    # Add recent users
    for user in recent_users:
        timeline_activities.append({
            'type': 'user',
            'title': f'New User: {user.username}',
            'time': user.date_joined.strftime('%H:%M'),
            'icon': 'fas fa-user-plus',
            'color': 'info'
        })
    
    # Sort by time (most recent first)
    timeline_activities.sort(key=lambda x: x['time'], reverse=True)
    
    context = {
        'today_sales': today_sales,
        'today_transactions': today_transactions,
        'total_inventory': total_inventory,
        'low_stock_products': low_stock_products,
        'total_users': total_users,
        'active_users': active_users,
        'timeline_activities': timeline_activities[:6],  # Show only top 6
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'accounts/dashboard.html', context)
    

@role_required(['admin', 'manager'])
def user_management(request):
    from .models import CustomUser
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