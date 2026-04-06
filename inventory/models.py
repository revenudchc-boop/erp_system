from django.db import models
from accounts.models import Account

class Warehouse(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class ProductCategory(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class Product(models.Model):
    # نوع المنتج الأساسي (سلعة/خدمة)
    PRODUCT_TYPE_CHOICES = (
        ('goods', 'سلعة (ملموسة)'),
        ('service', 'خدمة (غير ملموسة)'),
    )
    
    # استخدام المنتج (للتفرقة بين المواد الخام والمنتجات النهائية)
    PRODUCT_USAGE_CHOICES = (
        ('raw_material', 'مادة خام (للشراء فقط)'),
        ('finished_good', 'منتج نهائي (للبيع فقط)'),
        ('service', 'خدمة (للبيع فقط)'),
    )
    
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='goods')
    product_usage = models.CharField(max_length=20, choices=PRODUCT_USAGE_CHOICES, default='finished_good')
    
    code = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=50, blank=True)
    name_ar = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    unit = models.CharField(max_length=20, default='قطعة')
    valuation_method = models.CharField(max_length=20, default='weighted_average')
    
    # حقول خاصة بالسلع فقط
    current_stock = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    avg_cost = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    min_stock = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    max_stock = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    
    # حقول مشتركة
    selling_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    purchase_price = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    
    # حسابات محاسبية مرتبطة
    inventory_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_products')
    cost_of_sales_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='cogs_products')
    revenue_account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='revenue_products')
    
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=14.0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        type_icon = "📦" if self.product_type == 'goods' else "🛠️"
        usage_text = ""
        if self.product_usage == 'raw_material':
            usage_text = " (مادة خام)"
        elif self.product_usage == 'finished_good':
            usage_text = " (منتج نهائي)"
        elif self.product_usage == 'service':
            usage_text = " (خدمة)"
        return f"{type_icon} {self.code} - {self.name_ar}{usage_text}"

    class Meta:
        ordering = ['code']


class InventoryTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('purchase_in', 'شراء وارد'),
        ('sales_out', 'بيع صادر'),
        ('return_in', 'مرتجع وارد'),
        ('return_out', 'مرتجع صادر'),
        ('issue_out', 'صرف للإنتاج'),
        ('adjustment_in', 'تسوية زيادة'),
        ('adjustment_out', 'تسوية نقص'),
        ('transfer_in', 'تحويل وارد'),
        ('transfer_out', 'تحويل صادر'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='transactions')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='transactions')
    type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=18, decimal_places=4)
    unit_cost = models.DecimalField(max_digits=18, decimal_places=4)
    total_cost = models.DecimalField(max_digits=18, decimal_places=2)
    reference_type = models.CharField(max_length=20, blank=True)
    reference_id = models.PositiveIntegerField(null=True, blank=True)
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.code} - {self.type} - {self.quantity}"

    class Meta:
        ordering = ['-date']


class StockBalance(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_balances')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='stock_balances')
    quantity = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    avg_cost = models.DecimalField(max_digits=18, decimal_places=4, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['product', 'warehouse']

    def __str__(self):
        return f"{self.product.code} - {self.warehouse.code}: {self.quantity}"