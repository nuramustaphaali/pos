from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


# 🔐 Superuser-only access to Django admin
def superuser_only(request):
    return request.user.is_active and request.user.is_superuser

# Override default admin permission check
admin.site.has_permission = superuser_only


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('inventory/', include('inventory.urls')),
    path('sales/', include('sales.urls')),
    path('accounts/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)