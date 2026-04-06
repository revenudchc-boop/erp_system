from django.db import models

# Create your models here.
from django.db import models
from accounts.models import Account
from currencies.models import Currency

class Supplier(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    tax_number = models.CharField(max_length=50, blank=True)
    commercial_record = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    payment_terms = models.IntegerField(null=True, blank=True, help_text="أيام السداد")
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True)
    account = models.OneToOneField(Account, on_delete=models.PROTECT, related_name='supplier')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']