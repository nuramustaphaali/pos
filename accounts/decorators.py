# accounts/decorators.py
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages

def role_required(allowed_roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated and request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, 'Access denied. Insufficient permissions.')
                return redirect('login')
        return _wrapped_view
    return decorator

# Specific role decorators
admin_required = role_required(['admin'])
manager_required = role_required(['admin', 'manager'])
cashier_required = role_required(['admin', 'manager', 'cashier'])