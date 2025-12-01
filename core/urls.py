# core/urls.py (add to existing file)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('settings/', views.system_settings, name='system_settings'),
    path('field-builder/', views.field_builder, name='field_builder'),
    path('field-builder/field/<int:field_id>/edit/', views.edit_field, name='edit_field'),
    path('field-builder/field/<int:field_id>/delete/', views.delete_field, name='delete_field'),
    path('dynamic-form/', views.dynamic_form_test, name='dynamic_form_test'),
    path('api/form-data/<str:content_type>/<int:object_id>/', views.get_form_data, name='get_form_data'),
]