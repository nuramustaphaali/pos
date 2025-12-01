# core/admin.py
from django.contrib import admin
from .models import FieldCategory, CustomField, FieldValue

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