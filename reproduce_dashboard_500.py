import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from orders.models import Contact, Company
from orders.views import supplier_dashboard, home
import traceback
import logging

# Disable logging
logging.disable(logging.CRITICAL)

def reproduce():
    print("Setting up test data...")
    import random
    suffix = random.randint(10000, 99999)
    
    # Create company
    company, _ = Company.objects.get_or_create(company_name=f"Test Company {suffix}")
    
    # 1. Test as Supplier (Should work)
    print("\n--- Test Case 1: Supplier accessing Dashboard ---")
    supplier_user = User.objects.create_user(f'supplier_{suffix}', f'supplier_{suffix}@test.com', 'password')
    Contact.objects.create(
        user=supplier_user, 
        company=company, 
        name=f"Supplier {suffix}", 
        role='supplier', 
        approval_status='approved'
    )
    
    factory = RequestFactory()
    request = factory.get('/supplier/dashboard/')
    request.user = supplier_user
    
    try:
        response = supplier_dashboard(request)
        print(f"Supplier Dashboard Status Code: {response.status_code}")
    except Exception:
        print("CRASHED: Supplier Dashboard")
        traceback.print_exc()

    # 2. Test as Admin (No Contact) accessing Home (uses base.html)
    print("\n--- Test Case 2: Admin (No Contact) accessing Home ---")
    admin_user = User.objects.create_superuser(f'admin_{suffix}', f'admin_{suffix}@test.com', 'password')
    request = factory.get('/')
    request.user = admin_user
    
    try:
        response = home(request)
        print(f"Admin Home Status Code: {response.status_code}")
    except Exception:
        print("CRASHED: Admin Home")
        traceback.print_exc()

    # Cleanup
    supplier_user.delete()
    admin_user.delete()
    company.delete()

if __name__ == "__main__":
    reproduce()
