from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import JournalEntry, JournalLine
from accounts.models import Account
from cost_centers.models import CostCenter


@login_required
def entry_list(request):
    entries = JournalEntry.objects.all().order_by('-date')
    return render(request, 'journal/list.html', {'entries': entries})


@login_required
def entry_detail(request, id):
    entry = get_object_or_404(JournalEntry, id=id)
    lines = JournalLine.objects.filter(entry_id=id)
    return JsonResponse({
        'id': entry.id,
        'date': entry.date.isoformat(),
        'description': entry.description,
        'reference': entry.reference,
        'is_posted': entry.is_posted,
        'is_adjustment': entry.is_adjustment,
        'adjustment_type': entry.adjustment_type,
        'adjustment_reference': entry.adjustment_reference,
        'adjustment_notes': entry.adjustment_notes,
        'lines': [{
            'id': l.id,
            'account_id': l.account_id,
            'debit': float(l.debit),
            'credit': float(l.credit),
            'cost_center_id': l.cost_center_id
        } for l in lines]
    })


@login_required
def entry_create(request):
    if request.method == 'POST':
        # التحقق إذا كان الطلب JSON من الواجهة الجديدة
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            
            with transaction.atomic():
                entry = JournalEntry.objects.create(
                    date=data['date'],
                    description=data['description'],
                    reference=data.get('reference', ''),
                    is_adjustment=data.get('is_adjustment', False),
                    adjustment_type=data.get('adjustment_type', 'none'),
                    adjustment_reference=data.get('adjustment_reference', ''),
                    adjustment_notes=data.get('adjustment_notes', '')
                )
                
                for line_data in data['lines']:
                    JournalLine.objects.create(
                        entry=entry,
                        account_id=line_data['account_id'],
                        debit=line_data['debit'],
                        credit=line_data['credit'],
                        cost_center_id=line_data.get('cost_center_id', None)
                    )
                
                return JsonResponse({'id': entry.id, 'message': 'تم إضافة القيد بنجاح'})
        
        # الكود القديم للطلبات العادية (HTML form)
        with transaction.atomic():
            entry = JournalEntry.objects.create(
                date=request.POST.get('date'),
                description=request.POST.get('description'),
                reference=request.POST.get('reference', ''),
                is_adjustment=request.POST.get('is_adjustment') == 'on',
                adjustment_type=request.POST.get('adjustment_type', 'none'),
                adjustment_reference=request.POST.get('adjustment_reference', ''),
                adjustment_notes=request.POST.get('adjustment_notes', '')
            )
            
            accounts = request.POST.getlist('account[]')
            debits = request.POST.getlist('debit[]')
            credits = request.POST.getlist('credit[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            total_debit = 0
            total_credit = 0
            
            for i in range(len(accounts)):
                if accounts[i]:
                    debit = float(debits[i]) if debits[i] else 0
                    credit = float(credits[i]) if credits[i] else 0
                    total_debit += debit
                    total_credit += credit
                    
                    cost_center_id = cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    
                    JournalLine.objects.create(
                        entry=entry,
                        account_id=accounts[i],
                        debit=debit,
                        credit=credit,
                        cost_center_id=cost_center_id
                    )
            
            if abs(total_debit - total_credit) > 0.01:
                messages.error(request, 'مجموع المدين لا يساوي مجموع الدائن')
                return redirect('entry_create')
            
            messages.success(request, 'تم إضافة القيد بنجاح')
            return redirect('entry_list')
    
    accounts = Account.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    return render(request, 'journal/form.html', {
        'accounts': accounts,
        'cost_centers': cost_centers,
        'title': 'إضافة قيد جديد'
    })


@login_required
def entry_update(request, id):
    entry = get_object_or_404(JournalEntry, id=id)
    if entry.is_posted:
        messages.error(request, 'لا يمكن تعديل قيد مرحل')
        return redirect('entry_list')
    
    if request.method == 'POST':
        # التحقق إذا كان الطلب JSON
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            
            with transaction.atomic():
                entry.date = data['date']
                entry.description = data['description']
                entry.reference = data.get('reference', '')
                entry.is_adjustment = data.get('is_adjustment', False)
                entry.adjustment_type = data.get('adjustment_type', 'none')
                entry.adjustment_reference = data.get('adjustment_reference', '')
                entry.adjustment_notes = data.get('adjustment_notes', '')
                entry.save()
                
                JournalLine.objects.filter(entry_id=id).delete()
                
                for line_data in data['lines']:
                    JournalLine.objects.create(
                        entry=entry,
                        account_id=line_data['account_id'],
                        debit=line_data['debit'],
                        credit=line_data['credit'],
                        cost_center_id=line_data.get('cost_center_id', None)
                    )
                
                return JsonResponse({'id': entry.id, 'message': 'تم تحديث القيد بنجاح'})
        
        # الكود القديم للطلبات العادية
        with transaction.atomic():
            entry.date = request.POST.get('date')
            entry.description = request.POST.get('description')
            entry.reference = request.POST.get('reference', '')
            entry.is_adjustment = request.POST.get('is_adjustment') == 'on'
            entry.adjustment_type = request.POST.get('adjustment_type', 'none')
            entry.adjustment_reference = request.POST.get('adjustment_reference', '')
            entry.adjustment_notes = request.POST.get('adjustment_notes', '')
            entry.save()
            
            JournalLine.objects.filter(entry_id=id).delete()
            
            accounts = request.POST.getlist('account[]')
            debits = request.POST.getlist('debit[]')
            credits = request.POST.getlist('credit[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            total_debit = 0
            total_credit = 0
            
            for i in range(len(accounts)):
                if accounts[i]:
                    debit = float(debits[i]) if debits[i] else 0
                    credit = float(credits[i]) if credits[i] else 0
                    total_debit += debit
                    total_credit += credit
                    
                    cost_center_id = cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    
                    JournalLine.objects.create(
                        entry=entry,
                        account_id=accounts[i],
                        debit=debit,
                        credit=credit,
                        cost_center_id=cost_center_id
                    )
            
            if abs(total_debit - total_credit) > 0.01:
                messages.error(request, 'مجموع المدين لا يساوي مجموع الدائن')
                return redirect('entry_update', id=id)
            
            messages.success(request, 'تم تحديث القيد بنجاح')
            return redirect('entry_list')
    
    accounts = Account.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    lines = JournalLine.objects.filter(entry_id=id)
    return render(request, 'journal/form.html', {
        'accounts': accounts,
        'cost_centers': cost_centers,
        'entry': entry,
        'lines': lines,
        'title': 'تعديل قيد'
    })


@login_required
def entry_delete(request, id):
    entry = get_object_or_404(JournalEntry, id=id)
    if entry.is_posted:
        messages.error(request, 'لا يمكن حذف قيد مرحل')
        return redirect('entry_list')
    
    if request.method == 'POST':
        entry.delete()
        messages.success(request, 'تم حذف القيد بنجاح')
        return redirect('entry_list')
    
    return render(request, 'journal/delete.html', {'entry': entry})


@login_required
def entry_post(request, id):
    entry = get_object_or_404(JournalEntry, id=id)
    if entry.is_posted:
        messages.warning(request, 'القيد مرحل بالفعل')
        return redirect('entry_list')
    
    with transaction.atomic():
        for line in entry.lines.all():
            account = line.account
            if line.debit > 0:
                account.balance += line.debit
            else:
                account.balance -= line.credit
            account.save()
        
        entry.is_posted = True
        entry.posted_at = timezone.now()
        entry.posted_by = request.user
        entry.save()
    
    messages.success(request, 'تم ترحيل القيد بنجاح')
    return redirect('entry_list')


@login_required
def entry_unpost(request, id):
    """إلغاء ترحيل قيد محاسبي"""
    entry = get_object_or_404(JournalEntry, id=id)
    
    if not entry.is_posted:
        messages.warning(request, 'القيد غير مرحل أصلاً')
        return redirect('entry_list')
    
    with transaction.atomic():
        for line in entry.lines.all():
            account = line.account
            if line.debit > 0:
                account.balance -= line.debit
            else:
                account.balance += line.credit
            account.save()
        
        entry.is_posted = False
        entry.posted_at = None
        entry.unposted_by = request.user
        entry.unposted_at = timezone.now()
        entry.save()
    
    messages.success(request, f'✅ تم إلغاء ترحيل القيد رقم {entry.id} بنجاح')
    return redirect('entry_list')


@login_required
def trial_balance(request):
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    if not year or not month:
        return render(request, 'journal/trial.html')
    
    accounts = Account.objects.all()
    
    result = []
    total_debit = 0
    total_credit = 0
    
    for acc in accounts:
        balance = abs(acc.balance)
        if acc.balance != 0:
            if acc.type in ['asset', 'expense']:
                total_debit += balance
                result.append({
                    'code': acc.code,
                    'name': acc.name,
                    'debit': balance,
                    'credit': 0,
                    'balance': balance,
                    'side': 'مدين'
                })
            else:
                total_credit += balance
                result.append({
                    'code': acc.code,
                    'name': acc.name,
                    'debit': 0,
                    'credit': balance,
                    'balance': balance,
                    'side': 'دائن'
                })
    
    return render(request, 'journal/trial.html', {
        'result': result,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'year': year,
        'month': month
    })


# ==================== دوال API للواجهة الجديدة ====================

@login_required
@csrf_exempt
@require_http_methods(["GET"])
def api_entries_list(request):
    """API: جلب قائمة القيود"""
    entries = JournalEntry.objects.all().order_by('-date')
    data = []
    for entry in entries:
        lines = JournalLine.objects.filter(entry_id=entry.id)
        data.append({
            'id': entry.id,
            'date': entry.date.isoformat(),
            'description': entry.description,
            'reference': entry.reference,
            'is_posted': entry.is_posted,
            'is_adjustment': entry.is_adjustment,
            'adjustment_type': entry.adjustment_type,
            'posted_at': entry.posted_at.isoformat() if entry.posted_at else None,
            'lines': [{
                'id': l.id,
                'account_id': l.account_id,
                'debit': float(l.debit),
                'credit': float(l.credit)
            } for l in lines]
        })
    return JsonResponse(data, safe=False)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_entry_create(request):
    """API: إنشاء قيد جديد"""
    try:
        data = json.loads(request.body)
        
        with transaction.atomic():
            entry = JournalEntry.objects.create(
                date=data['date'],
                description=data['description'],
                reference=data.get('reference', ''),
                is_adjustment=data.get('is_adjustment', False),
                adjustment_type=data.get('adjustment_type', 'none'),
                adjustment_reference=data.get('adjustment_reference', ''),
                adjustment_notes=data.get('adjustment_notes', '')
            )
            
            for line_data in data['lines']:
                JournalLine.objects.create(
                    entry=entry,
                    account_id=line_data['account_id'],
                    debit=line_data['debit'],
                    credit=line_data['credit'],
                    cost_center_id=line_data.get('cost_center_id', None)
                )
            
            return JsonResponse({'id': entry.id, 'message': 'تم إضافة القيد بنجاح'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_entry_update(request, id):
    """API: تحديث قيد موجود"""
    try:
        entry = get_object_or_404(JournalEntry, id=id)
        if entry.is_posted:
            return JsonResponse({'error': 'لا يمكن تعديل قيد مرحل'}, status=400)
        
        data = json.loads(request.body)
        
        with transaction.atomic():
            entry.date = data['date']
            entry.description = data['description']
            entry.reference = data.get('reference', '')
            entry.is_adjustment = data.get('is_adjustment', False)
            entry.adjustment_type = data.get('adjustment_type', 'none')
            entry.adjustment_reference = data.get('adjustment_reference', '')
            entry.adjustment_notes = data.get('adjustment_notes', '')
            entry.save()
            
            JournalLine.objects.filter(entry_id=id).delete()
            
            for line_data in data['lines']:
                JournalLine.objects.create(
                    entry=entry,
                    account_id=line_data['account_id'],
                    debit=line_data['debit'],
                    credit=line_data['credit'],
                    cost_center_id=line_data.get('cost_center_id', None)
                )
            
            return JsonResponse({'id': entry.id, 'message': 'تم تحديث القيد بنجاح'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@csrf_exempt
@require_http_methods(["POST"])
def api_entry_post(request, id):
    """API: ترحيل قيد"""
    try:
        entry = get_object_or_404(JournalEntry, id=id)
        if entry.is_posted:
            return JsonResponse({'error': 'القيد مرحل بالفعل'}, status=400)
        
        with transaction.atomic():
            for line in entry.lines.all():
                account = line.account
                if line.debit > 0:
                    account.balance += line.debit
                else:
                    account.balance -= line.credit
                account.save()
            
            entry.is_posted = True
            entry.posted_at = timezone.now()
            entry.posted_by = request.user
            entry.save()
        
        return JsonResponse({'message': 'تم ترحيل القيد بنجاح'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ==================== دوال معاينة وطباعة القيد ====================

@login_required
def journal_entry_detail(request, id):
    entry = get_object_or_404(JournalEntry, id=id)
    lines = entry.lines.all()
    
    total_debit = sum(line.debit for line in lines)
    total_credit = sum(line.credit for line in lines)
    
    return render(request, 'journal/entry_detail.html', {
        'entry': entry,
        'lines': lines,
        'total_debit': total_debit,
        'total_credit': total_credit
    })


@login_required
def journal_entry_print(request, id):
    entry = get_object_or_404(JournalEntry, id=id)
    lines = entry.lines.all()
    
    total_debit = sum(line.debit for line in lines)
    total_credit = sum(line.credit for line in lines)
    
    return render(request, 'journal/entry_print.html', {
        'entry': entry,
        'lines': lines,
        'total_debit': total_debit,
        'total_credit': total_credit
    })