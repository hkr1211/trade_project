import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')
django.setup()

from django.contrib import admin
from django.contrib.auth.models import User
from orders.admin import UserAdmin

print("Django setup complete.")

# Check if User is registered
if User in admin.site._registry:
    print("User model is registered.")
    registered_admin = admin.site._registry[User]
    print(f"Registered Admin Class: {registered_admin.__class__.__name__}")
    
    if isinstance(registered_admin, UserAdmin):
        print("SUCCESS: Custom UserAdmin is active.")
        print(f"Actions: {registered_admin.actions}")
    else:
        print("FAILURE: Default or other UserAdmin is active.")
else:
    print("FAILURE: User model is NOT registered.")

# Check site header
print(f"Site Header: {admin.site.site_header}")
