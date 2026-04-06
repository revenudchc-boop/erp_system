from django.db import models
from accounts.models import Account
from customers.models import Customer
from suppliers.models import Supplier
from inventory.models import Product, Warehouse
from currencies.models import Currency
from journal.models import JournalEntry
from cost_centers.models import CostCenter
from decimal import Decimal


class PurchaseInvoice(models.Model):
    """فاتورة مشتريات"""
    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('posted', 'مرحل'),
        ('cancelled', 'ملغي'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, default=1.0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_invoice')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"شراء {self.invoice_number} - {self.supplier.name}"

    class Meta:
        ordering = ['-date']


class PurchaseLine(models.Model):
    """سطر فاتورة مشتريات"""
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    discount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=14.0)
    total = models.DecimalField(max_digits=18, decimal_places=2, editable=False, default=0)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_lines')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        qty = Decimal(str(self.quantity)) if self.quantity else Decimal('0')
        price = Decimal(str(self.unit_price)) if self.unit_price else Decimal('0')
        disc = Decimal(str(self.discount)) if self.discount else Decimal('0')
        
        self.total = (qty * price) - disc
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.code} - {self.quantity} x {self.unit_price}"


class PurchaseReturn(models.Model):
    """مردود مشتريات"""
    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('posted', 'مرحل'),
        ('cancelled', 'ملغي'),
    )
    
    return_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    original_invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.PROTECT, related_name='returns')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, default=1.0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_return')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"مردود مشتريات {self.return_number} - {self.supplier.name}"


class PurchaseReturnLine(models.Model):
    """سطر مردود مشتريات"""
    return_invoice = models.ForeignKey(PurchaseReturn, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    discount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=14.0)
    total = models.DecimalField(max_digits=18, decimal_places=2, editable=False, default=0)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchase_return_lines')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        qty = Decimal(str(self.quantity)) if self.quantity else Decimal('0')
        price = Decimal(str(self.unit_price)) if self.unit_price else Decimal('0')
        disc = Decimal(str(self.discount)) if self.discount else Decimal('0')
        
        self.total = (qty * price) - disc
        super().save(*args, **kwargs)


class SalesInvoice(models.Model):
    """فاتورة مبيعات"""
    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('posted', 'مرحل'),
        ('cancelled', 'ملغي'),
    )
    
    invoice_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, default=1.0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_invoice')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"بيع {self.invoice_number} - {self.customer.name}"

    class Meta:
        ordering = ['-date']


class SalesLine(models.Model):
    """سطر فاتورة مبيعات"""
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=1)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    discount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=14.0)
    total = models.DecimalField(max_digits=18, decimal_places=2, editable=False, default=0)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_lines')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        qty = Decimal(str(self.quantity)) if self.quantity else Decimal('0')
        price = Decimal(str(self.unit_price)) if self.unit_price else Decimal('0')
        disc = Decimal(str(self.discount)) if self.discount else Decimal('0')
        
        self.total = (qty * price) - disc
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.code} - {self.quantity} x {self.unit_price}"


class SalesReturn(models.Model):
    """مردود مبيعات"""
    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('posted', 'مرحل'),
        ('cancelled', 'ملغي'),
    )
    
    return_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    original_invoice = models.ForeignKey(SalesInvoice, on_delete=models.PROTECT, related_name='returns')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, default=1)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, default=1.0)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_return')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"مردود مبيعات {self.return_number} - {self.customer.name}"


class SalesReturnLine(models.Model):
    """سطر مردود مبيعات"""
    return_invoice = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    discount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=14.0)
    total = models.DecimalField(max_digits=18, decimal_places=2, editable=False, default=0)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales_return_lines')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        qty = Decimal(str(self.quantity)) if self.quantity else Decimal('0')
        price = Decimal(str(self.unit_price)) if self.unit_price else Decimal('0')
        disc = Decimal(str(self.discount)) if self.discount else Decimal('0')
        
        self.total = (qty * price) - disc
        super().save(*args, **kwargs)