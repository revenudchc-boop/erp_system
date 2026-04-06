from django.db import models

class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name_ar = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50, blank=True)
    symbol = models.CharField(max_length=5, blank=True)
    is_base = models.BooleanField(default=False)
    exchange_rate = models.DecimalField(max_digits=18, decimal_places=6, default=1.0)
    decimal_places = models.PositiveSmallIntegerField(default=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.code} - {self.name_ar}"

    class Meta:
        ordering = ['code']


class ExchangeRateHistory(models.Model):
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='history')
    rate = models.DecimalField(max_digits=18, decimal_places=6)
    date = models.DateField()
    source = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['currency', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.currency.code}: {self.rate} - {self.date}"