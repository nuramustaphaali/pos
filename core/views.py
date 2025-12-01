from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import SystemSettings, FieldCategory, CustomField, CustomField, DynamicFormData
from .forms import SystemSettingsForm, FieldCategoryForm, CustomFieldForm
from django.http import JsonResponse
from .utils import DynamicFormEngine

# core/views.py (Dashboard with real data)
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
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/home.html')

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

    

@login_required
def system_settings(request):
    # Get or create the system settings instance
    settings, created = SystemSettings.objects.get_or_create(pk=1)
    
    if request.method == 'POST':
        form = SystemSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'System settings updated successfully!')
            return redirect('system_settings')
    else:
        form = SystemSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'core/system_settings.html', context)

def get_current_settings():
    """Helper function to get current system settings"""
    settings, created = SystemSettings.objects.get_or_create(pk=1)
    return settings

@login_required
def field_builder(request):
    if request.method == 'POST':
        if 'create_category' in request.POST:
            category_form = FieldCategoryForm(request.POST)
            if category_form.is_valid():
                category_form.save()
                messages.success(request, 'Category created successfully!')
                return redirect('field_builder')
        elif 'create_field' in request.POST:
            field_form = CustomFieldForm(request.POST)
            if field_form.is_valid():
                field_form.save()
                messages.success(request, 'Custom field created successfully!')
                return redirect('field_builder')
    else:
        category_form = FieldCategoryForm()
        field_form = CustomFieldForm()
    
    categories = FieldCategory.objects.prefetch_related('fields').all()
    
    context = {
        'categories': categories,
        'category_form': category_form,
        'field_form': field_form,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'core/field_builder.html', context)

@login_required
def edit_field(request, field_id):
    field = get_object_or_404(CustomField, id=field_id)
    
    if request.method == 'POST':
        form = CustomFieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            messages.success(request, 'Field updated successfully!')
            return redirect('field_builder')
    else:
        form = CustomFieldForm(instance=field)
    
    context = {
        'form': form,
        'field': field,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'core/edit_field.html', context)

@login_required
def delete_field(request, field_id):
    field = get_object_or_404(CustomField, id=field_id)
    field_name = field.name
    field.delete()
    messages.success(request, f'Field "{field_name}" deleted successfully!')
    return redirect('field_builder')


@login_required
def dynamic_form_test(request):
    """Test view to demonstrate dynamic form rendering"""
    if request.method == 'POST':
        try:
            # Process form data
            form_data = {}
            for key, value in request.POST.items():
                if key.startswith('field_') and value:  # Dynamic fields start with 'field_'
                    field_name = key.replace('field_', '')
                    form_data[field_name] = value
            
            # Process with dynamic form engine
            dynamic_form = DynamicFormEngine.process_form_data(
                content_type='test_form',
                object_id=1,
                form_data=form_data
            )
            
            messages.success(request, 'Form data saved successfully!')
            return redirect('dynamic_form_test')
            
        except Exception as e:
            messages.error(request, f'Error saving form: {str(e)}')
    
    # Render dynamic form
    form_html = DynamicFormEngine.render_form_fields('test_form')
    
    context = {
        'form_html': form_html,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'core/dynamic_form_test.html', context)

@login_required
def get_form_data(request, content_type, object_id):
    """AJAX endpoint to get form data"""
    try:
        data = DynamicFormEngine.get_form_data(content_type, object_id)
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})