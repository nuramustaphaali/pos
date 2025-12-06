from django import template
from django.utils import timezone

from core.models import SystemSettings, License
from inventory.models import Product, ProductCategory
from sales.models import POSOrder

register = template.Library()


@register.simple_tag
def plan_usage():
    """Return subscription/plan usage info for the dashboard."""
    system = SystemSettings.objects.first()
    if not system:
        return {}

    try:
        license_obj = system.license
    except License.DoesNotExist:
        return {}

    if not license_obj.is_active or license_obj.is_expired:
        active = False
    else:
        active = True

    plan = license_obj.plan
    today = timezone.now().date()

    products_count = Product.objects.count()
    categories_count = ProductCategory.objects.count()
    today_orders_count = POSOrder.objects.filter(
        created_at__date=today,
        status="completed",
    ).count()

    def percent(current, maximum):
        if not maximum:
            return None
        try:
            return max(0, min(100, int((current / maximum) * 100)))
        except ZeroDivisionError:
            return None

    return {
        "plan_name": plan.name,
        "plan_code": plan.code,
        "license_active": active,
        "license_expires_at": license_obj.expires_at,
        "max_products": plan.max_products or None,
        "max_categories": plan.max_categories or None,
        "max_orders_per_day": plan.max_orders_per_day or None,
        "products_count": products_count,
        "categories_count": categories_count,
        "today_orders_count": today_orders_count,
        "products_percent": percent(products_count, plan.max_products),
        "categories_percent": percent(categories_count, plan.max_categories),
        "orders_percent": percent(today_orders_count, plan.max_orders_per_day),
    }