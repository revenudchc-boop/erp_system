from django.db import models

# Create your models here.
from django.db import models

class Account(models.Model):
    TYPE_CHOICES = [
        ('asset', 'أصل'),
        ('liability', 'خصم'),
        ('equity', 'حقوق ملكية'),
        ('revenue', 'إيراد'),
        ('expense', 'مصروف'),
    ]
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"