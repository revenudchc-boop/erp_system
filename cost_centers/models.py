from django.db import models

# Create your models here.
from django.db import models
from accounts.models import Account

class CostCenter(models.Model):
    TYPE_CHOICES = [
        ('operational', 'تشغيلي'),
        ('support', 'دعم'),
        ('investment', 'استثماري'),
        ('project', 'مشروع'),
        ('department', 'قسم'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='operational')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    manager = models.CharField(max_length=100, blank=True)
    budget = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class CostElement(models.Model):
    TYPE_CHOICES = [
        ('direct_material', 'مواد مباشرة'),
        ('direct_labor', 'أجور مباشرة'),
        ('indirect_material', 'مواد غير مباشرة'),
        ('indirect_labor', 'أجور غير مباشرة'),
        ('depreciation', 'إهلاك'),
        ('rent', 'إيجار'),
        ('utilities', 'مرافق'),
        ('other', 'أخرى'),
    ]
    
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='other')
    account = models.ForeignKey(Account, on_delete=models.SET_NULL, null=True, blank=True, related_name='cost_elements')
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        ordering = ['code']


class CostAllocationRule(models.Model):
    METHOD_CHOICES = [
        ('percentage', 'نسبة مئوية'),
        ('fixed', 'قيمة ثابتة'),
        ('rate', 'معدل لكل وحدة'),
        ('activity', 'على أساس النشاط'),
    ]
    
    FREQUENCY_CHOICES = [
        ('monthly', 'شهري'),
        ('quarterly', 'ربع سنوي'),
        ('yearly', 'سنوي'),
        ('one_time', 'مرة واحدة'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    source_type = models.CharField(max_length=20)  # 'account', 'cost_element'
    source_id = models.PositiveIntegerField()
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='monthly')
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CostAllocationTarget(models.Model):
    rule = models.ForeignKey(CostAllocationRule, on_delete=models.CASCADE, related_name='targets')
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, related_name='allocations')
    allocation_value = models.DecimalField(max_digits=18, decimal_places=6)  # نسبة أو قيمة
    notes = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rule.name} -> {self.cost_center.name}"


class CostAllocationRun(models.Model):
    STATUS_CHOICES = [
        ('pending', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
    ]
    
    rule = models.ForeignKey(CostAllocationRule, on_delete=models.CASCADE, related_name='runs')
    run_date = models.DateTimeField(auto_now_add=True)
    period_start = models.DateField()
    period_end = models.DateField()
    total_amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    journal_entry = models.ForeignKey('journal.JournalEntry', on_delete=models.SET_NULL, null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.rule.name} - {self.period_start} to {self.period_end}"