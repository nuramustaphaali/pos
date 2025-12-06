from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, ProductCategory, InventoryTransaction
from .forms import ProductForm, ProductCategoryForm
from django.core.exceptions import PermissionDenied
from core.utils import check_limit_or_block

def dashboard(request):
    return render(request, 'inventory/dashboard.html')

@login_required
def inventory_dashboard(request):
    # Get statistics
    total_products = Product.objects.count()
    total_stock = Product.objects.aggregate(total=Sum('stock_quantity'))['total'] or 0
    low_stock_count = Product.objects.filter(stock_status='low_stock').count()
    out_of_stock_count = Product.objects.filter(stock_status='out_of_stock').count()
    
    # Get recent products
    recent_products = Product.objects.order_by('-created_at')[:5]
    
    # Separate low stock and out-of-stock products
    low_stock_products = Product.objects.filter(stock_status='low_stock')[:5]
    out_of_stock_products = Product.objects.filter(stock_status='out_of_stock')[:5]
    
    context = {
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'recent_products': recent_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,  # Added this line
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/dashboard.html', context)

@login_required
def product_list(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    stock_status = request.GET.get('stock_status', '')
    
    products = Product.objects.select_related('category').all()
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(sku__icontains=query) | 
            Q(barcode__icontains=query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if status:
        products = products.filter(status=status)
    
    if stock_status:
        products = products.filter(stock_status=stock_status)
    
    # Pagination
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = ProductCategory.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_status': status,
        'selected_stock_status': stock_status,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/product_list.html', context)


# inventory/views.py (complete add and edit functions)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Sum
from django.core.paginator import Paginator
from .models import Product, ProductCategory, InventoryTransaction, StockAdjustment
from .forms import ProductForm, ProductCategoryForm
@login_required
def add_product(request):
    """
    Add a new product to inventory, respecting plan limits.
    """
    # Check limit before even showing the form
    try:
        check_limit_or_block("products")
    except PermissionDenied as e:
        messages.error(request, str(e))
        return redirect('inventory:product_list')

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # Check again in case another user added product in between
                check_limit_or_block("products")

                # Save the product
                product = form.save()

                # Create initial stock transaction if quantity > 0
                if product.stock_quantity > 0:
                    InventoryTransaction.objects.create(
                        product=product,
                        transaction_type='in',
                        quantity=product.stock_quantity,
                        reference=f'Initial stock for {product.name}',
                        created_by=request.user.username
                    )

                messages.success(request, f'Product "{product.name}" added successfully!')
                return redirect('inventory:product_list')
            except PermissionDenied as e:
                messages.error(request, str(e))
                return redirect('inventory:product_list')
            except Exception as e:
                messages.error(request, f'Error adding product: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()

    context = {
        'form': form,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/add_product.html', context)



@login_required
def edit_product(request, product_id):
    """
    Edit an existing product
    """
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            try:
                # Get old stock quantity before save
                old_stock = product.stock_quantity
                
                # Save the updated product
                updated_product = form.save()
                
                # If stock quantity changed, create adjustment transaction
                new_stock = updated_product.stock_quantity
                if old_stock != new_stock:
                    diff = new_stock - old_stock
                    transaction_type = 'in' if diff > 0 else 'out'
                    quantity = abs(diff)
                    
                    InventoryTransaction.objects.create(
                        product=updated_product,
                        transaction_type=transaction_type,
                        quantity=quantity,
                        reference=f'Stock adjustment for {updated_product.name}',
                        created_by=request.user.username
                    )
                
                messages.success(request, f'Product "{updated_product.name}" updated successfully!')
                return redirect('inventory:product_detail', product_id=updated_product.id)
            except Exception as e:
                messages.error(request, f'Error updating product: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/edit_product.html', context)



@login_required
def product_detail(request, product_id):
    """
    View product details with transactions and adjustments
    """
    product = get_object_or_404(Product, id=product_id)
    transactions = InventoryTransaction.objects.filter(product=product).order_by('-created_at')[:10]
    adjustments = StockAdjustment.objects.filter(product=product).order_by('-created_at')[:10]
    
    context = {
        'product': product,
        'transactions': transactions,
        'adjustments': adjustments,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/product_detail.html', context)


@login_required
def product_category_list(request):
    categories = ProductCategory.objects.all()
    
    context = {
        'categories': categories,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/category_list.html', context)

@login_required
def add_category(request):
    """
    Add a new product category, respecting plan limits.
    """
    try:
        check_limit_or_block("categories")
    except PermissionDenied as e:
        messages.error(request, str(e))
        return redirect('inventory:category_list')

    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            try:
                # Check again in case someone else added a category
                check_limit_or_block("categories")
                category = form.save()
                messages.success(request, f'Category "{category.name}" created successfully!')
                return redirect('inventory:category_list')
            except PermissionDenied as e:
                messages.error(request, str(e))
                return redirect('inventory:category_list')
            except Exception as e:
                messages.error(request, f'Error creating category: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductCategoryForm()

    context = {
        'form': form,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/add_category.html', context)

@login_required
def adjust_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        transaction_type = request.POST.get('transaction_type', 'adjustment')
        notes = request.POST.get('notes', '')
        
        # Update stock
        if transaction_type == 'in':
            product.stock_quantity += quantity
        elif transaction_type == 'out':
            product.stock_quantity -= quantity
        else:  # adjustment
            product.stock_quantity = quantity
        
        product.save()
        
        # Create transaction record
        InventoryTransaction.objects.create(
            product=product,
            transaction_type=transaction_type,
            quantity=quantity,
            notes=notes,
            created_by=request.user.username
        )
        
        messages.success(request, f'Stock adjusted for {product.name}')
        return redirect('inventory:product_detail', product_id=product.id)
    
    context = {
        'product': product,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/adjust_stock.html', context)


# inventory/views.py (add to existing views)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F, Sum
from django.core.paginator import Paginator
from .models import Product, ProductCategory, InventoryTransaction, StockAdjustment
from .forms import ProductForm, ProductCategoryForm

@login_required
def restock_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        reason = request.POST.get('reason', '')
        reference = request.POST.get('reference_number', '')
        
        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0')
            return redirect('inventory:restock_product', product_id=product.id)
        
        # Create stock adjustment record
        StockAdjustment.objects.create(
            product=product,
            adjustment_type='restock',
            quantity=quantity,
            reason=reason,
            reference_number=reference,
            performed_by=request.user.username
        )
        
        messages.success(request, f'Successfully restocked {quantity} units of {product.name}')
        return redirect('inventory:product_detail', product_id=product.id)
    
    context = {
        'product': product,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/restock_product.html', context)

@login_required
def reduce_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        reason = request.POST.get('reason', '')
        reference = request.POST.get('reference_number', '')
        
        if quantity <= 0:
            messages.error(request, 'Quantity must be greater than 0')
            return redirect('inventory:reduce_stock', product_id=product.id)
        
        if quantity > product.stock_quantity:
            messages.error(request, f'Cannot reduce stock by {quantity}. Current stock is {product.stock_quantity}')
            return redirect('inventory:reduce_stock', product_id=product.id)
        
        # Create stock adjustment record
        StockAdjustment.objects.create(
            product=product,
            adjustment_type='reduce',
            quantity=quantity,
            reason=reason,
            reference_number=reference,
            performed_by=request.user.username
        )
        
        messages.success(request, f'Successfully reduced {quantity} units of {product.name}')
        return redirect('inventory:product_detail', product_id=product.id)
    
    context = {
        'product': product,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/reduce_stock.html', context)

@login_required
def stock_adjustment_history(request):
    adjustments = StockAdjustment.objects.select_related('product').all().order_by('-created_at')
    
    # Filtering
    product_id = request.GET.get('product', '')
    adjustment_type = request.GET.get('type', '')
    
    if product_id:
        adjustments = adjustments.filter(product_id=product_id)
    
    if adjustment_type:
        adjustments = adjustments.filter(adjustment_type=adjustment_type)
    
    # Pagination
    paginator = Paginator(adjustments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    products = Product.objects.all()
    
    context = {
        'page_obj': page_obj,
        'products': products,
        'selected_product': product_id,
        'selected_type': adjustment_type,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/stock_adjustment_history.html', context)

@login_required
def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    transactions = InventoryTransaction.objects.filter(product=product).order_by('-created_at')[:10]
    adjustments = StockAdjustment.objects.filter(product=product).order_by('-created_at')[:10]
    
    context = {
        'product': product,
        'transactions': transactions,
        'adjustments': adjustments,
        'user_role': request.user.role,
        'user_name': request.user.get_full_name() or request.user.username,
    }
    return render(request, 'inventory/product_detail.html', context)