from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Max
from .models import BankAccount, CashRegister, BankStatementLine
from accounts.models import Account
from currencies.models import Currency
from journal.models import JournalLine, JournalEntry

# ==================== البنوك ====================

@login_required
def banks_list(request):
    banks = BankAccount.objects.all()
    return render(request, 'banks/banks_list.html', {'banks': banks})

@login_required
def bank_create(request):
    if request.method == 'POST':
        bank_name = request.POST.get('bank_name')
        branch = request.POST.get('branch', '')
        account_number = request.POST.get('account_number')
        iban = request.POST.get('iban', '')
        currency_id = request.POST.get('currency')
        opening_balance = request.POST.get('opening_balance', 0)
        notes = request.POST.get('notes', '')
        
        # البحث عن حساب "نقدية بالبنك" أو إنشاؤه
        parent_account, _ = Account.objects.get_or_create(
            code='112',
            defaults={
                'name': 'نقدية بالبنك',
                'type': 'asset',
                'parent': Account.objects.filter(code='11').first(),
                'is_active': True
            }
        )
        
        # توليد كود تلقائي للبنك
        last_bank = Account.objects.filter(parent=parent_account).order_by('-code').first()
        if last_bank and last_bank.code.isdigit():
            last_num = int(last_bank.code)
            new_code = str(last_num + 1).zfill(len(last_bank.code))
        else:
            new_code = '112001'  # بداية التسلسل
        
        # إنشاء حساب البنك
        account = Account.objects.create(
            code=new_code,
            name=f"{bank_name} - {account_number}",
            type='asset',
            parent=parent_account,
            balance=opening_balance,
            is_active=True
        )
        
        # إنشاء الحساب البنكي
        BankAccount.objects.create(
            account=account,
            bank_name=bank_name,
            branch=branch,
            account_number=account_number,
            iban=iban,
            currency_id=currency_id,
            opening_balance=opening_balance,
            current_balance=opening_balance,
            notes=notes
        )
        
        messages.success(request, 'تم إضافة الحساب البنكي بنجاح')
        return redirect('banks_list')
    
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'banks/bank_form.html', {'currencies': currencies, 'title': 'إضافة حساب بنكي'})

@login_required
def bank_detail(request, id):
    bank = get_object_or_404(BankAccount, id=id)
    return JsonResponse({
        'id': bank.id,
        'bank_name': bank.bank_name,
        'branch': bank.branch,
        'account_number': bank.account_number,
        'iban': bank.iban,
        'currency_id': bank.currency_id,
        'opening_balance': float(bank.opening_balance),
        'current_balance': float(bank.current_balance),
        'notes': bank.notes
    })

@login_required
def bank_update(request, id):
    bank = get_object_or_404(BankAccount, id=id)
    
    if request.method == 'POST':
        bank.bank_name = request.POST.get('bank_name')
        bank.branch = request.POST.get('branch', '')
        bank.account_number = request.POST.get('account_number')
        bank.iban = request.POST.get('iban', '')
        bank.currency_id = request.POST.get('currency')
        bank.notes = request.POST.get('notes', '')
        bank.save()
        
        # تحديث الحساب المحاسبي (الاسم فقط)
        bank.account.name = f"{bank.bank_name} - {bank.account_number}"
        bank.account.save()
        
        messages.success(request, 'تم تحديث الحساب البنكي بنجاح')
        return redirect('banks_list')
    
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'banks/bank_form.html', {
        'bank': bank,
        'currencies': currencies,
        'title': 'تعديل حساب بنكي'
    })

@login_required
def bank_delete(request, id):
    bank = get_object_or_404(BankAccount, id=id)
    
    if request.method == 'POST':
        try:
            account = bank.account
            bank.delete()
            account.delete()
            messages.success(request, 'تم حذف الحساب البنكي بنجاح')
            return redirect('banks_list')
        except Exception as e:
            messages.error(request, f'⚠️ لا يمكن حذف هذا الحساب: {str(e)}')
            return redirect('banks_list')
    
    return render(request, 'banks/bank_delete.html', {'bank': bank})

@login_required
def bank_statement(request, id):
    bank = get_object_or_404(BankAccount, id=id)
    
    # جلب حركات البنك من القيود المحاسبية
    lines = JournalLine.objects.filter(
        account=bank.account,
        entry__is_posted=True
    ).select_related('entry').order_by('entry__date', 'entry__id')
    
    result = []
    balance = bank.opening_balance
    
    for line in lines:
        if line.debit > 0:
            balance += line.debit
        else:
            balance -= line.credit
        
        result.append({
            'date': line.entry.date,
            'description': line.entry.description,
            'reference': line.entry.reference,
            'debit': float(line.debit),
            'credit': float(line.credit),
            'balance': balance
        })
    
    return render(request, 'banks/bank_statement.html', {
        'bank': bank,
        'transactions': result,
        'balance': balance
    })

# ==================== الصناديق ====================

@login_required
def cash_list(request):
    cash_registers = CashRegister.objects.all()
    return render(request, 'banks/cash_list.html', {'cash_registers': cash_registers})

@login_required
def cash_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        currency_id = request.POST.get('currency')
        opening_balance = request.POST.get('opening_balance', 0)
        notes = request.POST.get('notes', '')
        
        # البحث عن حساب "نقدية بالصندوق" أو إنشاؤه
        parent_account, _ = Account.objects.get_or_create(
            code='111',
            defaults={
                'name': 'نقدية بالصندوق',
                'type': 'asset',
                'parent': Account.objects.filter(code='11').first(),
                'is_active': True
            }
        )
        
        # توليد كود تلقائي للصندوق
        last_cash = Account.objects.filter(parent=parent_account).order_by('-code').first()
        if last_cash and last_cash.code.isdigit():
            last_num = int(last_cash.code)
            new_code = str(last_num + 1).zfill(len(last_cash.code))
        else:
            new_code = '111001'  # بداية التسلسل
        
        # إنشاء حساب الصندوق
        account = Account.objects.create(
            code=new_code,
            name=f"صندوق - {name}",
            type='asset',
            parent=parent_account,
            balance=opening_balance,
            is_active=True
        )
        
        # إنشاء الصندوق
        CashRegister.objects.create(
            account=account,
            name=name,
            currency_id=currency_id,
            opening_balance=opening_balance,
            current_balance=opening_balance,
            notes=notes
        )
        
        messages.success(request, 'تم إضافة الصندوق بنجاح')
        return redirect('cash_list')
    
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'banks/cash_form.html', {'currencies': currencies, 'title': 'إضافة صندوق جديد'})

@login_required
def cash_update(request, id):
    cash = get_object_or_404(CashRegister, id=id)
    
    if request.method == 'POST':
        cash.name = request.POST.get('name')
        cash.currency_id = request.POST.get('currency')
        cash.notes = request.POST.get('notes', '')
        cash.save()
        
        # تحديث الحساب المحاسبي
        cash.account.name = f"صندوق - {cash.name}"
        cash.account.save()
        
        messages.success(request, 'تم تحديث الصندوق بنجاح')
        return redirect('cash_list')
    
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'banks/cash_form.html', {
        'cash': cash,
        'currencies': currencies,
        'title': 'تعديل صندوق'
    })

@login_required
def cash_delete(request, id):
    cash = get_object_or_404(CashRegister, id=id)
    
    if request.method == 'POST':
        try:
            account = cash.account
            cash.delete()
            account.delete()
            messages.success(request, 'تم حذف الصندوق بنجاح')
            return redirect('cash_list')
        except Exception as e:
            messages.error(request, f'⚠️ لا يمكن حذف هذا الصندوق: {str(e)}')
            return redirect('cash_list')
    
    return render(request, 'banks/cash_delete.html', {'cash': cash})