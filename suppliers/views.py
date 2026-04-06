from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Max, Q
from .models import Supplier
from accounts.models import Account
from currencies.models import Currency
from journal.models import JournalLine, JournalEntry

@login_required
def suppliers_list(request):
    suppliers = Supplier.objects.all()
    return render(request, 'suppliers/list.html', {'suppliers': suppliers})

@login_required
def suppliers_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        tax_number = request.POST.get('tax_number', '')
        commercial_record = request.POST.get('commercial_record', '')
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        payment_terms = request.POST.get('payment_terms') or None
        currency_id = request.POST.get('currency') or None
        parent_account_id = request.POST.get('parent_account') or None
        notes = request.POST.get('notes', '')
        
        # تحديد الحساب الأب
        if parent_account_id:
            parent_account = get_object_or_404(Account, id=parent_account_id)
        else:
            parent_account, _ = Account.objects.get_or_create(
                code='211',
                defaults={
                    'name': 'دائنون (موردون)',
                    'type': 'liability',
                    'parent': Account.objects.filter(code='21').first(),
                    'is_active': True
                }
            )
        
        # توليد كود تلقائي للمورد بناءً على الحساب الأب
        last_supplier_under_parent = Account.objects.filter(parent=parent_account).order_by('-code').first()
        
        if last_supplier_under_parent and last_supplier_under_parent.code.isdigit():
            last_num = int(last_supplier_under_parent.code)
            new_code = str(last_num + 1).zfill(len(last_supplier_under_parent.code))
        else:
            # إذا لم يوجد أي حساب تحت هذا الأب، نبدأ بكود يعتمد على كود الأب
            new_code = f"{parent_account.code}001"
        
        # إنشاء حساب المورد
        account = Account.objects.create(
            code=new_code,
            name=f"{name} (مورد)",
            type='liability',
            parent=parent_account,
            balance=0,
            is_active=True
        )
        
        # إنشاء المورد
        Supplier.objects.create(
            code=new_code,
            name=name,
            tax_number=tax_number,
            commercial_record=commercial_record,
            address=address,
            phone=phone,
            email=email,
            payment_terms=payment_terms,
            currency_id=currency_id,
            account=account,
            notes=notes
        )
        
        messages.success(request, 'تم إضافة المورد بنجاح')
        return redirect('suppliers_list')
    
    currencies = Currency.objects.filter(is_active=True)
    
    # جلب حسابات الموردين فقط (دائنون وما تحتها)
    main_parent = Account.objects.filter(code='211').first()
    if main_parent:
        parent_accounts = Account.objects.filter(
            Q(id=main_parent.id) | Q(parent=main_parent)
        ).filter(is_active=True)
    else:
        parent_accounts = Account.objects.none()
    
    return render(request, 'suppliers/form.html', {
        'currencies': currencies,
        'parent_accounts': parent_accounts,
        'title': 'إضافة مورد جديد'
    })

@login_required
def suppliers_detail(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    return JsonResponse({
        'id': supplier.id,
        'code': supplier.code,
        'name': supplier.name,
        'tax_number': supplier.tax_number,
        'commercial_record': supplier.commercial_record,
        'address': supplier.address,
        'phone': supplier.phone,
        'email': supplier.email,
        'payment_terms': supplier.payment_terms,
        'currency_id': supplier.currency_id,
        'balance': float(supplier.account.balance),
        'notes': supplier.notes
    })

@login_required
def suppliers_update(request, id):
    supplier = get_object_or_404(Supplier, id=id)

    if request.method == 'POST':
        supplier.name = request.POST.get('name')
        supplier.tax_number = request.POST.get('tax_number', '')
        supplier.commercial_record = request.POST.get('commercial_record', '')
        supplier.address = request.POST.get('address', '')
        supplier.phone = request.POST.get('phone', '')
        supplier.email = request.POST.get('email', '')
        supplier.payment_terms = request.POST.get('payment_terms') or None
        supplier.currency_id = request.POST.get('currency') or None
        supplier.notes = request.POST.get('notes', '')
        supplier.save()

        # تحديث الحساب المحاسبي
        supplier.account.name = supplier.name + ' (مورد)'
        supplier.account.save()

        messages.success(request, 'تم تحديث بيانات المورد بنجاح')
        return redirect('suppliers_list')

    currencies = Currency.objects.filter(is_active=True)
    return render(request, 'suppliers/form.html', {
        'supplier': supplier,
        'currencies': currencies,
        'title': 'تعديل بيانات مورد'
    })

@login_required
def suppliers_delete(request, id):
    supplier = get_object_or_404(Supplier, id=id)

    has_balance = supplier.account.balance != 0

    if request.method == 'POST':
        try:
            account = supplier.account
            supplier.delete()
            account.delete()
            messages.success(request, 'تم حذف المورد بنجاح')
            return redirect('suppliers_list')
        except Exception as e:
            messages.error(request, f'⚠️ لا يمكن حذف هذا المورد: {str(e)}')
            return redirect('suppliers_list')

    return render(request, 'suppliers/delete.html', {
        'supplier': supplier,
        'has_balance': has_balance
    })

@login_required
def suppliers_statement(request, id):
    supplier = get_object_or_404(Supplier, id=id)

    lines = JournalLine.objects.filter(
        account=supplier.account,
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

    return render(request, 'suppliers/statement.html', {
        'supplier': supplier,
        'transactions': result,
        'balance': balance
    })