# core/utils.py
import json
from django.core.exceptions import ValidationError
from .models import CustomField, FieldValue, DynamicFormData, FormDataEntry
import json
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone

from .models import CustomField, FieldValue, DynamicFormData, FormDataEntry, SystemSettings, License
from inventory.models import Product, ProductCategory
from sales.models import POSOrder


class DynamicFormEngine:
    """
    Engine to handle dynamic form creation, validation, and data storage
    """
    
    @staticmethod
    def get_fields_for_content_type(content_type):
        """Get all fields for a specific content type"""
        # For now, we'll return all fields - in real implementation you'd filter by content_type
        return CustomField.objects.filter(show_on_pos=True).order_by('category__name', 'order')
    
    @staticmethod
    def validate_field_value(field, value):
        """Validate field value based on field type and validation rules"""
        errors = []
        
        # Required field validation
        if field.required and not value:
            errors.append(f"{field.label} is required")
        
        # Type-specific validation
        if value:
            if field.field_type == 'email' and '@' not in value:
                errors.append(f"Invalid email format for {field.label}")
            elif field.field_type == 'phone' and not value.isdigit():
                errors.append(f"Phone number should contain only digits for {field.label}")
            elif field.field_type == 'number':
                try:
                    float(value)
                except ValueError:
                    errors.append(f"Invalid number format for {field.label}")
            elif field.field_type == 'percentage':
                try:
                    num_val = float(value)
                    if num_val < 0 or num_val > 100:
                        errors.append(f"Percentage should be between 0 and 100 for {field.label}")
                except ValueError:
                    errors.append(f"Invalid percentage format for {field.label}")
            elif field.field_type == 'dropdown' and field.dropdown_options:
                if value not in field.dropdown_options:
                    errors.append(f"Invalid option selected for {field.label}")
        
        # Custom validation rules
        if field.validation_rules:
            rules = field.validation_rules
            if 'min_length' in rules and len(str(value)) < rules['min_length']:
                errors.append(f"{field.label} must be at least {rules['min_length']} characters")
            if 'max_length' in rules and len(str(value)) > rules['max_length']:
                errors.append(f"{field.label} must be no more than {rules['max_length']} characters")
            if 'regex' in rules:
                import re
                if not re.match(rules['regex'], str(value)):
                    errors.append(f"{field.label} format is invalid")
        
        return errors
    
    @staticmethod
    def process_form_data(content_type, object_id, form_data):
        """Process and store form data"""
        # Validate all fields
        all_errors = []
        validated_data = {}
        
        for field_name, value in form_data.items():
            try:
                field = CustomField.objects.get(name=field_name)
                errors = DynamicFormEngine.validate_field_value(field, value)
                if errors:
                    all_errors.extend(errors)
                else:
                    validated_data[field_name] = value
            except CustomField.DoesNotExist:
                # Skip fields that don't exist
                continue
        
        if all_errors:
            raise ValidationError(all_errors)
        
        # Store in DynamicFormData
        dynamic_form, created = DynamicFormData.objects.get_or_create(
            content_type=content_type,
            object_id=object_id,
            defaults={'form_data': validated_data}
        )
        
        if not created:
            dynamic_form.form_data = validated_data
            dynamic_form.save()
        
        # Store individual entries for better querying
        FormDataEntry.objects.filter(content_type=content_type, object_id=object_id).delete()
        
        for field_name, value in validated_data.items():
            try:
                field = CustomField.objects.get(name=field_name)
                FormDataEntry.objects.get_or_create(
                    content_type=content_type,
                    object_id=object_id,
                    field_name=field_name,
                    defaults={
                        'field_value': value,
                        'field_type': field.field_type
                    }
                )
            except CustomField.DoesNotExist:
                continue
        
        return dynamic_form
    
    @staticmethod
    def get_form_data(content_type, object_id):
        """Retrieve form data for an object"""
        try:
            dynamic_form = DynamicFormData.objects.get(content_type=content_type, object_id=object_id)
            return dynamic_form.form_data
        except DynamicFormData.DoesNotExist:
            return {}
    
    @staticmethod
    def render_form_fields(content_type, prefix=''):
        """Generate HTML for form fields based on content type"""
        fields = DynamicFormEngine.get_fields_for_content_type(content_type)
        html_parts = []
        
        current_category = None
        for field in fields:
            # Add category header if new category
            if field.category.name != current_category:
                if current_category:
                    html_parts.append('</div>')  # Close previous category
                html_parts.append(f'<div class="category-section mb-4">')
                html_parts.append(f'<h6 class="gradient-text mb-3">{field.category.name}</h6>')
                html_parts.append('<div class="row">')
                current_category = field.category.name
            
            # Generate field HTML
            field_html = DynamicFormEngine.render_single_field(field, prefix)
            html_parts.append(f'<div class="col-md-6">{field_html}</div>')
        
        if current_category:
            html_parts.append('</div></div>')  # Close last category
        
        return ''.join(html_parts)
    
    @staticmethod
    def render_single_field(field, prefix=''):
        """Render a single field as HTML"""
        field_id = f"{prefix}{field.name}"
        field_name = f"{prefix}{field.name}"
        
        # Get stored value if exists
        stored_value = ""
        
        # Base field attributes
        attrs = {
            'id': field_id,
            'name': field_name,
            'class': 'form-control gradient-input',
            'placeholder': field.placeholder or field.label,
        }
        
        if field.required:
            attrs['required'] = 'required'
        
        # Generate field based on type
        if field.field_type == 'text':
            attrs['type'] = 'text'
            field_html = f'<input {DynamicFormEngine._dict_to_attrs(attrs)} value="{stored_value}">'
        
        elif field.field_type == 'number':
            attrs['type'] = 'number'
            if field.validation_rules.get('min'):
                attrs['min'] = field.validation_rules['min']
            if field.validation_rules.get('max'):
                attrs['max'] = field.validation_rules['max']
            field_html = f'<input {DynamicFormEngine._dict_to_attrs(attrs)} value="{stored_value}">'
        
        elif field.field_type == 'email':
            attrs['type'] = 'email'
            field_html = f'<input {DynamicFormEngine._dict_to_attrs(attrs)} value="{stored_value}">'
        
        elif field.field_type == 'phone':
            attrs['type'] = 'tel'
            field_html = f'<input {DynamicFormEngine._dict_to_attrs(attrs)} value="{stored_value}">'
        
        elif field.field_type == 'date':
            attrs['type'] = 'date'
            field_html = f'<input {DynamicFormEngine._dict_to_attrs(attrs)} value="{stored_value}">'
        
        elif field.field_type == 'datetime':
            attrs['type'] = 'datetime-local'
            field_html = f'<input {DynamicFormEngine._dict_to_attrs(attrs)} value="{stored_value}">'
        
        elif field.field_type == 'boolean':
            field_html = f'''
            <div class="form-check form-switch">
                <input class="form-check-input" type="checkbox" id="{field_id}" name="{field_name}" {"checked" if stored_value else ""}>
                <label class="form-check-label" for="{field_id}">{field.label}</label>
            </div>
            '''
        
        elif field.field_type == 'dropdown':
            options_html = []
            for option in field.dropdown_options:
                selected = 'selected' if option == stored_value else ''
                options_html.append(f'<option value="{option}" {selected}>{option}</option>')
            field_html = f'<select {DynamicFormEngine._dict_to_attrs(attrs)}>{"".join(options_html)}</select>'
        
        elif field.field_type == 'textarea':
            attrs['rows'] = '3'
            field_html = f'<textarea {DynamicFormEngine._dict_to_attrs(attrs)}>{stored_value}</textarea>'
        
        elif field.field_type == 'currency':
            attrs['type'] = 'text'
            attrs['class'] = 'form-control gradient-input currency-input'
            field_html = f'<input {DynamicFormEngine._dict_to_attrs(attrs)} value="{stored_value}">'
        
        elif field.field_type == 'percentage':
            attrs['type'] = 'number'
            attrs['min'] = '0'
            attrs['max'] = '100'
            attrs['step'] = '0.01'
            field_html = f'<input {DynamicFormEngine._dict_to_attrs(attrs)} value="{stored_value}">%'
        
        else:  # Default to text
            attrs['type'] = 'text'
            field_html = f'<input {DynamicFormEngine._dict_to_attrs(attrs)} value="{stored_value}">'
        
        # Wrap with label and help text
        wrapper_html = f'''
        <label for="{field_id}" class="form-label">
            {field.label}{' <span class="text-danger">*</span>' if field.required else ''}
        </label>
        {field_html}
        {f'<div class="form-text">{field.help_text}</div>' if field.help_text else ''}
        '''
        
        return wrapper_html
    
    @staticmethod
    def _dict_to_attrs(attrs):
        """Convert dictionary to HTML attributes string"""
        return ' '.join([f'{k}="{v}"' for k, v in attrs.items()])

# Validation helper functions
def validate_email(value):
    if '@' not in value:
        raise ValidationError('Invalid email format')

def validate_phone(value):
    if not value.replace('-', '').replace(' ', '').isdigit():
        raise ValidationError('Invalid phone number format')

def validate_number(value):
    try:
        float(value)
    except ValueError:
        raise ValidationError('Invalid number format')
        
        
# -----------------------------
# Licensing & Plan Limit Helpers
# -----------------------------

def get_current_license():
    """
    Returns the License object for this installation, or None.
    """
    system = SystemSettings.objects.first()
    if not system:
        return None

    try:
        return system.license
    except License.DoesNotExist:
        return None


def check_limit_or_block(limit_name: str):
    """
    Central function to enforce limits.

    limit_name can be:
      - "products"
      - "categories"
      - "orders_per_day"

    Raises PermissionDenied if limit exceeded or license invalid.
    """
    license_obj = get_current_license()

    # If no license or deactivated, block everything.
    if not license_obj or not license_obj.is_active or license_obj.is_expired:
        raise PermissionDenied(
            "Your license is inactive or has expired. Please contact the software provider."
        )

    plan = license_obj.plan

    today = timezone.now().date()

    # Map each limit to current usage + allowed max
    if limit_name == "products":
        max_allowed = plan.max_products
        current = Product.objects.count()
    elif limit_name == "categories":
        max_allowed = plan.max_categories
        current = ProductCategory.objects.count()
    elif limit_name == "orders_per_day":
        max_allowed = plan.max_orders_per_day
        current = POSOrder.objects.filter(created_at__date=today).count()
    else:
        # Unknown limit; do nothing
        return

    # 0 means unlimited
    if max_allowed and current >= max_allowed:
        # Message shown to client (keep it friendly / business-like)
        raise PermissionDenied(
            "You have reached the limit of your current subscription plan. "
            "Please contact the software provider to upgrade."
        )