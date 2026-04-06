from django.db import models
from django.conf import settings
from accounts.models import Account


class JournalEntry(models.Model):
    STATUS_CHOICES = (
        ('draft', 'مسودة'),
        ('posted', 'مرحل'),
        ('cancelled', 'ملغي'),
    )
    
    ADJUSTMENT_TYPES = (
        ('none', 'لا يوجد'),
        ('inventory', 'جرد مخزون'),
        ('bank', 'تسوية بنكية'),
        ('depreciation', 'إهلاك'),
        ('currency', 'فروق عملة'),
        ('accrual', 'مصروفات مستحقة'),
        ('prepaid', 'مصروفات مدفوعة مقدماً'),
    )
    
    date = models.DateField()
    description = models.TextField()
    reference = models.CharField(max_length=50, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_entries'
    )
    posted_at = models.DateTimeField(null=True, blank=True)
    is_posted = models.BooleanField(default=False)
    unposted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unposted_entries'
    )
    unposted_at = models.DateTimeField(null=True, blank=True)
    
    # حقول التسويات الجردية
    is_adjustment = models.BooleanField(default=False, help_text="هل هذا القيد تسوية جردية؟")
    adjustment_type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPES, default='none', help_text="نوع التسوية الجردية")
    adjustment_reference = models.CharField(max_length=100, blank=True, help_text="رقم المستند المرجعي (محضر جرد، كشف بنك، إلخ)")
    adjustment_notes = models.TextField(blank=True, help_text="ملاحظات إضافية عن التسوية")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        adj_prefix = "📋 " if self.is_adjustment else ""
        return f"{adj_prefix}{self.date} - {self.description[:50]}"

    class Meta:
        ordering = ['-date']


class JournalLine(models.Model):
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='lines')
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    currency = models.ForeignKey('currencies.Currency', on_delete=models.SET_NULL, null=True, blank=True)
    amount_foreign = models.DecimalField(max_digits=18, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True)
    cost_center = models.ForeignKey('cost_centers.CostCenter', on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_lines')
    cost_element = models.ForeignKey('cost_centers.CostElement', on_delete=models.SET_NULL, null=True, blank=True, related_name='journal_lines')
    cash_flow_category = models.CharField(max_length=20, blank=True)  # operating, investing, financing
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.account.name}: د {self.debit} / ا {self.credit}"


class AccountBalance(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    fiscal_year = models.PositiveSmallIntegerField()
    period = models.PositiveSmallIntegerField()  # 1-12 للشهر
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['account', 'fiscal_year', 'period']
        ordering = ['account', 'fiscal_year', 'period']

    def __str__(self):
        return f"{self.account.name} - {self.fiscal_year}/{self.period}: د{self.debit} / ا{self.credit}"