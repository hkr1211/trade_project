"""
检查admin actions是否正确注册
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')
django.setup()

from django.contrib import admin
from orders.models import Contact
from orders.admin import ContactAdmin

# 检查 ContactAdmin 是否正确注册
if Contact in admin.site._registry:
    registered_admin = admin.site._registry[Contact]
    print(f"✓ Contact model is registered")
    print(f"Admin Class: {registered_admin.__class__.__name__}")
    print(f"\nDefined actions attribute: {registered_admin.actions}")
    
    # 获取实际的 actions
    from django.contrib.auth.models import User
    from django.test import RequestFactory
    
    # 创建一个模拟的 superuser request
    factory = RequestFactory()
    request = factory.get('/admin/orders/contact/')
    request.user = User.objects.filter(is_superuser=True).first()
    
    if request.user:
        print(f"\nTest user: {request.user.username} (superuser: {request.user.is_superuser})")
        
        # 获取可用的 actions
        actions = registered_admin.get_actions(request)
        print(f"\nAvailable actions count: {len(actions)}")
        print(f"Actions: {list(actions.keys())}")
        
        # 检查每个自定义 action
        for action_name in ['approve_contacts', 'reject_contacts', 'reset_password']:
            if action_name in actions:
                func, name, desc = actions[action_name]
                print(f"\n✓ {action_name}:")
                print(f"  Description: {desc}")
                print(f"  Has permissions attr: {hasattr(func, 'permissions')}")
                if hasattr(func, 'permissions'):
                    print(f"  Permissions: {func.permissions}")
            else:
                print(f"\n✗ {action_name}: NOT FOUND")
    else:
        print("\n✗ No superuser found in database")
else:
    print("✗ Contact model is NOT registered")
