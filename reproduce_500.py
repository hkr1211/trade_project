import os
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from orders.models import Contact, Company, Inquiry, InquiryItem, Message
from orders.views import supplier_inquiry_detail
from django.http import Http404

def reproduce():
    print("Setting up test data...")
    # Create company and users
    company, _ = Company.objects.get_or_create(company_name="Test Company Repro")
    
    import random
    suffix = random.randint(1000, 9999)
    supplier_user = User.objects.create_user(f'supplier_repro_{suffix}', f'supplier_{suffix}@repro.com', 'password')
    buyer_user = User.objects.create_user(f'buyer_repro_{suffix}', f'buyer_{suffix}@repro.com', 'password')
    
    supplier_contact = Contact.objects.create(
        user=supplier_user, company=company, name=f"Supplier Repro {suffix}", role='supplier', approval_status='approved', email=f'supplier_{suffix}@repro.com'
    )
    buyer_contact = Contact.objects.create(
        user=buyer_user, company=company, name=f"Buyer Repro {suffix}", role='buyer', approval_status='approved', email=f'buyer_{suffix}@repro.com'
    )
    
    # Create Inquiry
    inquiry = Inquiry.objects.create(
        inquiry_number=f"INQ-REPRO-{suffix}",
        contact=buyer_contact,
        status='pending'
    )
    
    # Create Inquiry Item
    InquiryItem.objects.create(
        inquiry=inquiry,
        product_name="Test Product",
        material_name="Steel",
        quantity=100,
        quoted_price=10.0
    )
    
    # Create Message
    Message.objects.create(
        inquiry=inquiry,
        sender=buyer_user,
        content="Hello"
    )

    factory = RequestFactory()
    request = factory.get(f'/supplier/inquiries/{inquiry.id}/')
    request.user = supplier_user
    
    print("Attempting to render view...")
    try:
        response = supplier_inquiry_detail(request, inquiry.id)
        print(f"Response status code: {response.status_code}")
        if response.status_code == 200:
            print("Render successful.")
        else:
            print("Render returned non-200 status.")
    except Exception as e:
        print(f"Caught exception during render: {e}")
        import traceback
        traceback.print_exc()

    # Test case 2: Contact without user (if possible in DB, though model has null=True)
    print("\nTest Case 2: Buyer Contact has no user")
    buyer_contact.user = None
    buyer_contact.save()
    
    try:
        response = supplier_inquiry_detail(request, inquiry.id)
        print(f"Response status code: {response.status_code}")
    except Exception as e:
        print(f"Caught exception during render (No User): {e}")
        import traceback
        traceback.print_exc()

    # Test Case 3: Missing file on disk (Skipped due to storage limitations)
    # print("\nTest Case 3: Item with missing file")
    # ... skipped ...

    # Test Case 4: Admin user visiting home (Base template check)
    print("\nTest Case 4: Admin user visiting home")
    admin_user = User.objects.create_superuser(f'admin_{suffix}', f'admin_{suffix}@example.com', 'password')
    request.user = admin_user
    from orders.views import home
    try:
        response = home(request)
        print(f"Response status code (Admin Home): {response.status_code}")
    except Exception as e:
        print(f"Caught exception (Admin Home): {e}")
        # import traceback
        # traceback.print_exc()

    # Test Case 5: Message with attachment
    print("\nTest Case 5: Message with attachment")
    from orders.models import MessageAttachment
    from django.core.files.uploadedfile import SimpleUploadedFile
    
    request.user = supplier_user
    msg = Message.objects.create(inquiry=inquiry, sender=supplier_user, content="Attachment test")
    
    # Create a dummy file
    dummy_file = SimpleUploadedFile("test_att.txt", b"file_content")
    att = MessageAttachment.objects.create(message=msg, file=dummy_file)
    
    try:
        response = supplier_inquiry_detail(request, inquiry.id)
        print(f"Response status code (Message Attachment): {response.status_code}")
    except Exception as e:
        print(f"Caught exception (Message Attachment): {e}")
        import traceback
        traceback.print_exc()
        
    # Test Case 6: Inquiry with attachment
    print("\nTest Case 6: Inquiry with attachment")
    from orders.models import InquiryAttachment
    
    dummy_inq_file = SimpleUploadedFile("test_inq_att.txt", b"file_content")
    inq_att = InquiryAttachment.objects.create(inquiry=inquiry, file=dummy_inq_file)
    
    try:
        response = supplier_inquiry_detail(request, inquiry.id)
        print(f"Response status code (Inquiry Attachment): {response.status_code}")
    except Exception as e:
        print(f"Caught exception (Inquiry Attachment): {e}")
        import traceback
        traceback.print_exc()
        
    # Cleanup
    supplier_user.delete()
    buyer_user.delete()
    admin_user.delete()
    company.delete()

if __name__ == "__main__":
    reproduce()
