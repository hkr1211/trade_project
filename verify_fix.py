import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory
from orders.models import Contact, Company
from orders.admin import UserAdmin
from django.contrib import messages

def verify_fix():
    print("Setting up test data...")
    # Create a dummy company
    company, _ = Company.objects.get_or_create(company_name="Test Company")
    
    # Create a test user and contact
    username = "test_supplier_activation"
    email = "test_supplier_activation@example.com"
    
    # Clean up previous run
    User.objects.filter(username=username).delete()
    
    user = User.objects.create_user(username=username, email=email, password="password", is_active=False)
    contact = Contact.objects.create(
        user=user, 
        company=company, 
        name="Test Supplier", 
        email=email, 
        approval_status='pending'
    )
    
    print(f"Initial state: User is_active={user.is_active}, Contact approval_status={contact.approval_status}")
    
    # Setup Admin and Request
    site = AdminSite()
    admin = UserAdmin(User, site)
    factory = RequestFactory()
    request = factory.get('/')
    request.user = User.objects.create_superuser('admin_tester', 'admin@example.com', 'password')
    
    # Mock message_user to avoid errors
    def mock_message_user(request, message, level=messages.INFO, extra_tags='', fail_silently=False):
        print(f"Admin Message: {message}")
    admin.message_user = mock_message_user
    
    # Run the action
    print("Running activate_users action...")
    queryset = User.objects.filter(pk=user.pk)
    admin.activate_users(request, queryset)
    
    # Refresh from db
    user.refresh_from_db()
    contact.refresh_from_db()
    
    print(f"Final state: User is_active={user.is_active}, Contact approval_status={contact.approval_status}")
    
    if user.is_active and contact.approval_status == 'approved':
        print("SUCCESS: User activated and Contact approved!")
    else:
        print("FAILURE: User or Contact not updated correctly.")

if __name__ == "__main__":
    verify_fix()
