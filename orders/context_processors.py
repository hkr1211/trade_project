"""
Context processors for orders app
"""
from .models import Contact


def user_contact(request):
    """
    Add user's contact information to template context
    """
    contact = None
    if request.user.is_authenticated:
        try:
            contact = Contact.objects.get(user=request.user)
        except Contact.DoesNotExist:
            contact = None

    return {
        'user_contact': contact
    }
