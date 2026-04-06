from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from .models import CostCenter, CostElement, CostAllocationRule, CostAllocationTarget, CostAllocationRun
from accounts.models import Account
from journal.models import JournalEntry, JournalLine
from datetime import date

# ==================== مراكز التكلفة ====================

@login_required
def cost_centers_list(request):
    centers = CostCenter.objects.filter(parent__isnull=True)
    return render(request, 'cost_centers/list.html', {'centers': centers})

@login_required
def cost_centers_tree(request):
    def build_tree(centers, parent_id=None):
        tree = []
        for center in centers:
            if center.parent_id == parent_id:
                tree.append({
                    'id': center.id,
                    'code': center.code,
                    'name': center.name,
                    'type': center.type,
                    'budget': float(center.budget),
                    'children': build_tree(centers, center.id)
                })
        return tree
    
    centers = CostCenter.objects.all()
    return JsonResponse(build_tree(centers), safe=False)

@login_required
def cost_center_create(request):
    if request.method == 'POST':
        center = CostCenter(
            code=request.POST.get('code'),
            name=request.POST.get('name'),
            type=request.POST.get('type'),
            parent_id=request.POST.get('parent') or None,
            manager=request.POST.get('manager', ''),
            budget=request.POST.get('budget', 0),
            notes=request.POST.get('notes', '')
        )
        center.save()
        messages.success(request, 'تم إضافة مركز التكلفة بنجاح')
        return redirect('cost_centers_list')
    
    parents = CostCenter.objects.all()
    return render(request, 'cost_centers/center_form.html', {'parents': parents, 'title': 'إضافة مركز تكلفة'})

@login_required
def cost_center_update(request, id):
    center = get_object_or_404(CostCenter, id=id)
    
    if request.method == 'POST':
        center.code = request.POST.get('code')
        center.name = request.POST.get('name')
        center.type = request.POST.get('type')
        center.parent_id = request.POST.get('parent') or None
        center.manager = request.POST.get('manager', '')
        center.budget = request.POST.get('budget', 0)
        center.notes = request.POST.get('notes', '')
        center.save()
        messages.success(request, 'تم تحديث مركز التكلفة بنجاح')
        return redirect('cost_centers_list')
    
    parents = CostCenter.objects.exclude(id=id)
    return render(request, 'cost_centers/center_form.html', {'center': center, 'parents': parents, 'title': 'تعديل مركز تكلفة'})

@login_required
def cost_center_delete(request, id):
    center = get_object_or_404(CostCenter, id=id)
    
    if request.method == 'POST':
        center.delete()
        messages.success(request, 'تم حذف مركز التكلفة بنجاح')
        return redirect('cost_centers_list')
    
    return render(request, 'cost_centers/center_delete.html', {'center': center})

# ==================== عناصر التكلفة ====================

@login_required
def cost_elements_list(request):
    elements = CostElement.objects.all()
    return render(request, 'cost_centers/elements_list.html', {'elements': elements})

@login_required
def cost_element_create(request):
    if request.method == 'POST':
        element = CostElement(
            code=request.POST.get('code'),
            name=request.POST.get('name'),
            type=request.POST.get('type'),
            account_id=request.POST.get('account') or None,
            notes=request.POST.get('notes', '')
        )
        element.save()
        messages.success(request, 'تم إضافة عنصر التكلفة بنجاح')
        return redirect('cost_elements_list')
    
    accounts = Account.objects.filter(is_active=True)
    return render(request, 'cost_centers/element_form.html', {'accounts': accounts, 'title': 'إضافة عنصر تكلفة'})

@login_required
def cost_element_update(request, id):
    element = get_object_or_404(CostElement, id=id)
    
    if request.method == 'POST':
        element.code = request.POST.get('code')
        element.name = request.POST.get('name')
        element.type = request.POST.get('type')
        element.account_id = request.POST.get('account') or None
        element.notes = request.POST.get('notes', '')
        element.save()
        messages.success(request, 'تم تحديث عنصر التكلفة بنجاح')
        return redirect('cost_elements_list')
    
    accounts = Account.objects.filter(is_active=True)
    return render(request, 'cost_centers/element_form.html', {'element': element, 'accounts': accounts, 'title': 'تعديل عنصر تكلفة'})

@login_required
def cost_element_delete(request, id):
    element = get_object_or_404(CostElement, id=id)
    
    if request.method == 'POST':
        element.delete()
        messages.success(request, 'تم حذف عنصر التكلفة بنجاح')
        return redirect('cost_elements_list')
    
    return render(request, 'cost_centers/element_delete.html', {'element': element})

# ==================== قواعد التوزيع ====================

@login_required
def allocation_rules_list(request):
    rules = CostAllocationRule.objects.all()
    return render(request, 'cost_centers/rules_list.html', {'rules': rules})

@login_required
def allocation_rule_create(request):
    if request.method == 'POST':
        rule = CostAllocationRule(
            name=request.POST.get('name'),
            description=request.POST.get('description', ''),
            source_type=request.POST.get('source_type'),
            source_id=request.POST.get('source_id'),
            method=request.POST.get('method'),
            frequency=request.POST.get('frequency', 'monthly'),
            valid_from=request.POST.get('valid_from') or None,
            valid_to=request.POST.get('valid_to') or None
        )
        rule.save()
        
        # حفظ الأهداف
        cost_centers = request.POST.getlist('target_center[]')
        values = request.POST.getlist('target_value[]')
        
        for i in range(len(cost_centers)):
            if cost_centers[i]:
                CostAllocationTarget.objects.create(
                    rule=rule,
                    cost_center_id=cost_centers[i],
                    allocation_value=values[i] if values[i] else 0
                )
        
        messages.success(request, 'تم إضافة قاعدة التوزيع بنجاح')
        return redirect('allocation_rules_list')
    
    cost_centers = CostCenter.objects.filter(is_active=True)
    return render(request, 'cost_centers/rule_form.html', {'cost_centers': cost_centers, 'title': 'إضافة قاعدة توزيع'})

@login_required
def allocation_rule_update(request, id):
    rule = get_object_or_404(CostAllocationRule, id=id)
    
    if request.method == 'POST':
        rule.name = request.POST.get('name')
        rule.description = request.POST.get('description', '')
        rule.source_type = request.POST.get('source_type')
        rule.source_id = request.POST.get('source_id')
        rule.method = request.POST.get('method')
        rule.frequency = request.POST.get('frequency', 'monthly')
        rule.valid_from = request.POST.get('valid_from') or None
        rule.valid_to = request.POST.get('valid_to') or None
        rule.save()
        
        # تحديث الأهداف
        rule.targets.all().delete()
        cost_centers = request.POST.getlist('target_center[]')
        values = request.POST.getlist('target_value[]')
        
        for i in range(len(cost_centers)):
            if cost_centers[i]:
                CostAllocationTarget.objects.create(
                    rule=rule,
                    cost_center_id=cost_centers[i],
                    allocation_value=values[i] if values[i] else 0
                )
        
        messages.success(request, 'تم تحديث قاعدة التوزيع بنجاح')
        return redirect('allocation_rules_list')
    
    cost_centers = CostCenter.objects.filter(is_active=True)
    return render(request, 'cost_centers/rule_form.html', {
        'rule': rule,
        'cost_centers': cost_centers,
        'targets': rule.targets.all(),
        'title': 'تعديل قاعدة توزيع'
    })

@login_required
def allocation_rule_delete(request, id):
    rule = get_object_or_404(CostAllocationRule, id=id)
    
    if request.method == 'POST':
        rule.delete()
        messages.success(request, 'تم حذف قاعدة التوزيع بنجاح')
        return redirect('allocation_rules_list')
    
    return render(request, 'cost_centers/rule_delete.html', {'rule': rule})

@login_required
def run_allocation_rule(request, id):
    rule = get_object_or_404(CostAllocationRule, id=id)
    
    # حساب المبلغ الإجمالي من المصدر
    if rule.source_type == 'account':
        account = get_object_or_404(Account, id=rule.source_id)
        # حساب الرصيد خلال الفترة
        total_amount = account.balance
    else:
        total_amount = 0
    
    with transaction.atomic():
        # إنشاء قيد محاسبي للتوزيع
        entry = JournalEntry.objects.create(
            date=date.today(),
            description=f"توزيع {rule.name} - {date.today()}",
            is_posted=True,
            posted_at=date.today()
        )
        
        # توزيع المبلغ على مراكز التكلفة
        for target in rule.targets.all():
            if rule.method == 'percentage':
                amount = total_amount * (target.allocation_value / 100)
            else:
                amount = target.allocation_value
            
            # إضافة سطر القيد
            JournalLine.objects.create(
                entry=entry,
                account_id=rule.source_id,
                debit=amount,
                credit=0,
                cost_center=target.cost_center
            )
        
        # تسجيل عملية التوزيع
        CostAllocationRun.objects.create(
            rule=rule,
            period_start=date.today().replace(day=1),
            period_end=date.today(),
            total_amount=total_amount,
            status='completed',
            journal_entry=entry
        )
    
    messages.success(request, f'تم تنفيذ توزيع {rule.name} بنجاح')
    return redirect('allocation_rules_list')

# ==================== التقارير ====================

@login_required
def cost_center_report(request):
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    if not year or not month:
        return render(request, 'cost_centers/report.html')
    
    centers = CostCenter.objects.filter(is_active=True)
    result = []
    
    for center in centers:
        # حساب التكاليف المباشرة وغير المباشرة من القيود
        lines = JournalLine.objects.filter(
            cost_center=center,
            entry__is_posted=True,
            entry__date__year=year,
            entry__date__month=month
        )
        
        total_cost = sum(float(line.debit - line.credit) for line in lines)
        
        result.append({
            'code': center.code,
            'name': center.name,
            'type': center.get_type_display(),
            'budget': float(center.budget),
            'actual': total_cost,
            'variance': float(center.budget) - total_cost
        })
    
    return render(request, 'cost_centers/report.html', {
        'result': result,
        'year': year,
        'month': month
    })