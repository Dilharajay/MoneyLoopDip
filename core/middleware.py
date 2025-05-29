# middleware.py
from django.utils.functional import SimpleLazyObject
from .models import Customer

def get_customer(user):
    if not hasattr(user, '_cached_customer'):
        user._cached_customer = Customer.objects.get(user=user)
    return user._cached_customer

class CustomerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.customer = SimpleLazyObject(lambda: get_customer(request.user))
        return self.get_response(request)