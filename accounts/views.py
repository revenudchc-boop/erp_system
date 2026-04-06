from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Account

@login_required
def account_list(request):
    accounts = Account.objects.filter(parent__isnull=True)
    return render(request, 'accounts/list.html', {'accounts': accounts})

@login_required
def account_tree(request):
    def build_tree(accounts, parent_id=None):
        tree = []
        for acc in accounts:
            if acc.parent_id == parent_id:
                tree.append({
                    'id': acc.id,
                    'code': acc.code,
                    'name': acc.name,
                    'type': acc.type,
                    'balance': float(acc.balance),
                    'children': build_tree(accounts, acc.id)
                })
        return tree
    
    accounts = Account.objects.all()
    return JsonResponse(build_tree(accounts), safe=False)

@login_required
def account_api_list(request):
    """API: جلب قائمة الحسابات المسطحة"""
    accounts = Account.objects.all()
    data = [{
        'id': acc.id,
        'code': acc.code,
        'name': acc.name,
        'type': acc.type,
        'parent_id': acc.parent_id,
        'balance': float(acc.balance),
        'is_active': acc.is_active
    } for acc in accounts]
    return JsonResponse(data, safe=False)

@login_required
def account_create(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        name = request.POST.get('name')
        account_type = request.POST.get('type')
        parent_id = request.POST.get('parent') or None
        
        account = Account(
            code=code,
            name=name,
            type=account_type,
            parent_id=parent_id,
            balance=0,
            is_active=True
        )
        account.save()
        messages.success(request, 'تم إضافة الحساب بنجاح')
        return redirect('account_list')
    
    parents = Account.objects.filter(is_active=True)
    return render(request, 'accounts/form.html', {'parents': parents, 'title': 'إضافة حساب جديد'})

@login_required
def account_detail(request, id):
    account = get_object_or_404(Account, id=id)
    return JsonResponse({
        'id': account.id,
        'code': account.code,
        'name': account.name,
        'type': account.type,
        'parent_id': account.parent_id,
        'balance': float(account.balance)
    })

@login_required
def account_update(request, id):
    account = get_object_or_404(Account, id=id)
    
    if request.method == 'POST':
        account.code = request.POST.get('code')
        account.name = request.POST.get('name')
        account.type = request.POST.get('type')
        account.parent_id = request.POST.get('parent') or None
        account.save()
        messages.success(request, 'تم تحديث الحساب بنجاح')
        return redirect('account_list')
    
    parents = Account.objects.filter(is_active=True).exclude(id=id)
    return render(request, 'accounts/form.html', {'account': account, 'parents': parents, 'title': 'تعديل حساب'})

@login_required
def account_delete(request, id):
    account = get_object_or_404(Account, id=id)
    
    if request.method == 'POST':
        try:
            account.delete()
            messages.success(request, 'تم حذف الحساب بنجاح')
            return redirect('account_list')
        except Exception as e:
            messages.error(request, f'لا يمكن حذف هذا الحساب: {str(e)}')
            return redirect('account_list')
    
    return render(request, 'accounts/delete.html', {'account': account})