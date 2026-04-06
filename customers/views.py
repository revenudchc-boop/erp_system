from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Max
from .models import Customer
from accounts.models import Account
from currencies.models import Currency
from journal.models import JournalLine, JournalEntry


@login_required
def customers_list(request):
    customers = Customer.objects.all()
    return render(request, 'customers/list.html', {'customers': customers})


@login_required
def customers_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        tax_number = request.POST.get('tax_number', '')
        commercial_record = request.POST.get('commercial_record', '')
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        credit_limit = request.POST.get('credit_limit') or None
        currency_id = request.POST.get('currency') or None
        parent_account_id = request.POST.get('parent_account') or None
        notes = request.POST.get('notes', '')
        
        # تحديد الحساب الأب
        if parent_account_id:
            parent_account = get_object_or_404(Account, id=parent_account_id)
        else:
            parent_account, _ = Account.objects.get_or_create(
                code='12',
                defaults={
                    'name': 'ذمم مدينة (عملاء)',
                    'type': 'asset',
                    'parent': Account.objects.filter(code='1').first(),
                    'is_active': True
                }
            )
        
        # توليد كود تلقائي للعميل بناءً على الحساب الأب
        last_customer_under_parent = Account.objects.filter(parent=parent_account).order_by('-code').first()
        
        if last_customer_under_parent and last_customer_under_parent.code.isdigit():
            last_num = int(last_customer_under_parent.code)
            new_code = str(last_num + 1).zfill(len(last_customer_under_parent.code))
        else:
            # إذا لم يوجد أي حساب تحت هذا الأب، نبدأ بكود يعتمد على كود الأب
            new_code = f"{parent_account.code}001"
        
        # إنشاء حساب العميل
        account = Account.objects.create(
            code=new_code,
            name=f"{name} (عميل)",
            type='asset',
            parent=parent_account,
            balance=0,
            is_active=True
        )
        
        # إنشاء العميل
        Customer.objects.create(
            code=new_code,
            name=name,
            tax_number=tax_number,
            commercial_record=commercial_record,
            address=address,
            phone=phone,
            email=email,
            credit_limit=credit_limit,
            currency_id=currency_id,
            account=account,
            notes=notes
        )
        
        messages.success(request, 'تم إضافة العميل بنجاح')
        return redirect('customers_list')
    
    currencies = Currency.objects.filter(is_active=True)
    
    # جلب حسابات العملاء فقط (ذمم مدينة وما تحتها)
    main_parent = Account.objects.filter(code='12').first()
    if main_parent:
        parent_accounts = Account.objects.filter(
            Q(id=main_parent.id) | Q(parent=main_parent)
        ).filter(is_active=True)
    else:
        parent_accounts = Account.objects.none()
    
    return render(request, 'customers/form.html', {
        'currencies': currencies,
        'parent_accounts': parent_accounts,
        'title': 'إضافة عميل جديد'
    })


@login_required
def customers_detail(request, id):
    customer = get_object_or_404(Customer, id=id)
    return JsonResponse({
        'id': customer.id,
        'code': customer.code,
        'name': customer.name,
        'tax_number': customer.tax_number,
        'commercial_record': customer.commercial_record,
        'address': customer.address,
        'phone': customer.phone,
        'email': customer.email,
        'credit_limit': float(customer.credit_limit) if customer.credit_limit else None,
        'currency_id': customer.currency_id,
        'balance': float(customer.account.balance),
        'notes': customer.notes
    })


@login_required
def customers_update(request, id):
    customer = get_object_or_404(Customer, id=id)
    
    if request.method == 'POST':
        customer.name = request.POST.get('name')
        customer.tax_number = request.POST.get('tax_number', '')
        customer.commercial_record = request.POST.get('commercial_record', '')
        customer.address = request.POST.get('address', '')
        customer.phone = request.POST.get('phone', '')
        customer.email = request.POST.get('email', '')
        customer.credit_limit = request.POST.get('credit_limit') or None
        customer.currency_id = request.POST.get('currency') or None
        customer.notes = request.POST.get('notes', '')
        customer.save()
        
        # تحديث الحساب المحاسبي (الاسم فقط)
        customer.account.name = customer.name + ' (عميل)'
        customer.account.save()
        
        messages.success(request, 'تم تحديث بيانات العميل بنجاح')
        return redirect('customers_list')
    
    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'customers/form.html', {
        'customer': customer,
        'currencies': currencies,
        'title': 'تعديل بيانات عميل'
    })


@login_required
def customers_delete(request, id):
    customer = get_object_or_404(Customer, id=id)
    
    # التحقق من وجود رصيد
    has_balance = customer.account.balance != 0
    
    if request.method == 'POST':
        try:
            # حفظ الحساب المحاسبي قبل الحذف
            account = customer.account
            
            # حذف العميل أولاً
            customer.delete()
            
            # ثم حذف الحساب المحاسبي
            account.delete()
            
            messages.success(request, 'تم حذف العميل بنجاح')
            return redirect('customers_list')
        except Exception as e:
            messages.error(request, f'⚠️ لا يمكن حذف هذا العميل: {str(e)}')
            return redirect('customers_list')
    
    return render(request, 'customers/delete.html', {
        'customer': customer,
        'has_balance': has_balance
    })


@login_required
def customers_statement(request, id):
    customer = get_object_or_404(Customer, id=id)
    
    # جلب حركات العميل من القيود المحاسبية (المرحلة فقط)
    lines = JournalLine.objects.filter(
        account=customer.account,
        entry__is_posted=True
    ).select_related('entry').order_by('entry__date', 'entry__id')
    
    result = []
    balance = 0
    
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
    
    return render(request, 'customers/statement.html', {
        'customer': customer,
        'transactions': result,
        'balance': balance
    })