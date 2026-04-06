from django.db import models
from django.contrib.auth.models import User

class CompanySettings(models.Model):
    COMPANY_TYPE_CHOICES = (
        ('trading', 'شركة تجارية (بيع وشراء السلع)'),
        ('industrial', 'شركة صناعية/خدمية (مواد خام + خدمات)'),
    )
    
    company_type = models.CharField(max_length=20, choices=COMPANY_TYPE_CHOICES, default='trading')
    company_name = models.CharField(max_length=200, default='شركتي')
    tax_number = models.CharField(max_length=50, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"إعدادات الشركة - {self.get_company_type_display()}"

    class Meta:
        verbose_name = 'إعدادات الشركة'
        verbose_name_plural = 'إعدادات الشركة'