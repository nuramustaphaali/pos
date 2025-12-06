# core/admin.py
from django.contrib import admin
from .models import (
    FieldCategory,
    CustomField,
    FieldValue,
    SystemSettings,
    SubscriptionPlan,
    License,
)

@admin.register(FieldCategory)
class FieldCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at',)

@admin.register(CustomField)
class CustomFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'field_type', 'required', 'show_on_receipt', 'show_on_reports', 'order')
    list_filter = ('category', 'field_type', 'required', 'show_on_receipt', 'show_on_reports')
    search_fields = ('name', 'label')
    filter_horizontal = ('dropdown_options',) if 'dropdown_options' in locals() else ()

@admin.register(FieldValue)
class FieldValueAdmin(admin.ModelAdmin):
    list_display = ('field', 'content_type', 'object_id', 'value', 'created_at')
    list_filter = ('content_type', 'created_at')
    search_fields = ('value',)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ("business_name", "business_phone", "business_email", "currency")
    search_fields = ("business_name", "business_email")
    list_filter = ("currency",)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "code",
        "max_products",
        "max_categories",
        "max_orders_per_day",
        "allow_credit_sales",
        "allow_dynamic_fields",
    )
    list_filter = ("allow_credit_sales", "allow_dynamic_fields")
    search_fields = ("name", "code")


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = (
        "system",
        "plan",
        "license_key",
        "is_active",
        "expires_at",
        "started_at",
    )
    list_filter = ("plan", "is_active", "expires_at")
    search_fields = ("license_key", "system__business_name")