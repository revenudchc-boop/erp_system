from django.db import models
from accounts.models import Account
from currencies.models import Currency

class BankAccount(models.Model):
    account = models.OneToOneField(Account, on_delete=models.PROTECT, related_name='bank_account')
    bank_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50)
    iban = models.CharField(max_length=50, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"

    class Meta:
        ordering = ['bank_name']


class CashRegister(models.Model):
    account = models.OneToOneField(Account, on_delete=models.PROTECT, related_name='cash_register')
    name = models.CharField(max_length=100)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    opening_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    current_balance = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class BankStatementLine(models.Model):
    """سطور كشف الحساب البنكي"""
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name='statement_lines')
    transaction_date = models.DateField()
    description = models.CharField(max_length=200)
    debit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    reference = models.CharField(max_length=50, blank=True)
    journal_line = models.ForeignKey('journal.JournalLine', on_delete=models.SET_NULL, null=True, blank=True)
    is_reconciled = models.BooleanField(default=False)
    reconciled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bank_account.bank_name} - {self.transaction_date}"

    class Meta:
        ordering = ['-transaction_date']