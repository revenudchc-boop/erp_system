from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from accounts.models import Account
from journal.models import AccountBalance, JournalLine, JournalEntry
from datetime import datetime, timedelta
from calendar import monthrange


@login_required
def reports_dashboard(request):
    """صفحة التقارير الرئيسية"""
    return render(request, 'reports/dashboard.html')


@login_required
def income_statement(request):
    """قائمة الدخل"""
    year = request.GET.get('year')
    month = request.GET.get('month')
    end_date = request.GET.get('end_date')
    
    if year and month:
        end_date = f"{year}-{month}-{get_month_last_day(int(year), int(month))}"
    
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    # حساب الإيرادات
    revenues = Account.objects.filter(type='revenue', is_active=True)
    revenue_total = 0
    revenue_items = []
    
    for rev in revenues:
        balance = get_account_balance_up_to_date(rev.id, end_date)
        if balance != 0:
            revenue_total += balance
            revenue_items.append({
                'code': rev.code,
                'name': rev.name,
                'amount': balance
            })
    
    # حساب تكلفة المبيعات
    cogs = Account.objects.filter(type='cost_of_sales', is_active=True)
    cogs_total = 0
    cogs_items = []
    
    for cog in cogs:
        balance = get_account_balance_up_to_date(cog.id, end_date)
        if balance != 0:
            cogs_total += balance
            cogs_items.append({
                'code': cog.code,
                'name': cog.name,
                'amount': balance
            })
    
    # حساب المصروفات
    expenses = Account.objects.filter(type='expense', is_active=True)
    expense_total = 0
    expense_items = []
    
    for exp in expenses:
        balance = get_account_balance_up_to_date(exp.id, end_date)
        if balance != 0:
            expense_total += balance
            expense_items.append({
                'code': exp.code,
                'name': exp.name,
                'amount': balance
            })
    
    gross_profit = revenue_total - cogs_total
    net_income = gross_profit - expense_total
    
    context = {
        'revenues': revenue_items,
        'revenue_total': revenue_total,
        'cogs': cogs_items,
        'cogs_total': cogs_total,
        'expenses': expense_items,
        'expense_total': expense_total,
        'gross_profit': gross_profit,
        'net_income': net_income,
        'end_date': end_date
    }
    
    return render(request, 'reports/income_statement.html', context)


@login_required
def balance_sheet(request):
    """قائمة المركز المالي"""
    as_of_date = request.GET.get('as_of_date')
    
    if not as_of_date:
        as_of_date = datetime.now().strftime('%Y-%m-%d')
    
    # الأصول
    assets = Account.objects.filter(type='asset', is_active=True)
    assets_total = 0
    assets_items = []
    
    for asset in assets:
        balance = get_account_balance_up_to_date(asset.id, as_of_date)
        if balance != 0:
            assets_total += balance
            assets_items.append({
                'code': asset.code,
                'name': asset.name,
                'amount': balance
            })
    
    # الخصوم
    liabilities = Account.objects.filter(type='liability', is_active=True)
    liabilities_total = 0
    liabilities_items = []
    
    for liability in liabilities:
        balance = get_account_balance_up_to_date(liability.id, as_of_date)
        if balance != 0:
            liabilities_total += balance
            liabilities_items.append({
                'code': liability.code,
                'name': liability.name,
                'amount': balance
            })
    
    # حقوق الملكية
    equities = Account.objects.filter(type='equity', is_active=True)
    equities_total = 0
    equities_items = []
    
    for equity in equities:
        balance = get_account_balance_up_to_date(equity.id, as_of_date)
        if balance != 0:
            equities_total += balance
            equities_items.append({
                'code': equity.code,
                'name': equity.name,
                'amount': balance
            })
    
    total_liabilities_equity = liabilities_total + equities_total
    
    context = {
        'assets': assets_items,
        'assets_total': assets_total,
        'liabilities': liabilities_items,
        'liabilities_total': liabilities_total,
        'equities': equities_items,
        'equities_total': equities_total,
        'total_liabilities_equity': total_liabilities_equity,
        'as_of_date': as_of_date
    }
    
    return render(request, 'reports/balance_sheet.html', context)


@login_required
def cash_flow(request):
    """قائمة التدفقات النقدية"""
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    if not start_date or not end_date:
        # افتراضي: آخر 30 يوم
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    # الحصول على الحسابات النقدية (حسابات البنوك والصناديق)
    cash_accounts = Account.objects.filter(
        is_active=True
    ).filter(
        name__icontains='بنك'
    ) | Account.objects.filter(
        name__icontains='صندوق'
    )
    
    # حساب التدفقات
    inflows = 0  # المقبوضات
    outflows = 0  # المدفوعات
    
    for account in cash_accounts:
        # الحركات خلال الفترة
        lines = JournalLine.objects.filter(
            account=account,
            entry__is_posted=True,
            entry__date__gte=start_date,
            entry__date__lte=end_date
        )
        
        for line in lines:
            if line.debit > 0:
                inflows += line.debit
            else:
                outflows += line.credit
    
    net_cash_flow = inflows - outflows
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'inflows': inflows,
        'outflows': outflows,
        'net_cash_flow': net_cash_flow
    }
    
    return render(request, 'reports/cash_flow.html', context)


@login_required
def adjustments_report(request):
    """تقرير التسويات الجردية"""
    entries = JournalEntry.objects.filter(is_adjustment=True).order_by('-date')
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    adj_type = request.GET.get('type')
    
    if start_date:
        entries = entries.filter(date__gte=start_date)
    if end_date:
        entries = entries.filter(date__lte=end_date)
    if adj_type:
        entries = entries.filter(adjustment_type=adj_type)
    
    # حساب إجمالي المبالغ لكل قيد
    for entry in entries:
        total = 0
        for line in entry.lines.all():
            total += line.debit
        entry.total_amount = total
    
    return render(request, 'reports/adjustments.html', {
        'entries': entries,
        'start_date': start_date,
        'end_date': end_date,
        'selected_type': adj_type
    })


# دوال مساعدة
def get_account_balance_up_to_date(account_id, date):
    """حساب رصيد الحساب حتى تاريخ محدد"""
    account = Account.objects.get(id=account_id)
    balance = account.balance
    
    # حساب الحركات بعد تاريخ معين (إذا كان هناك ترحيلات لاحقة)
    lines = JournalLine.objects.filter(
        account_id=account_id,
        entry__is_posted=True,
        entry__date__gt=date
    )
    
    for line in lines:
        if line.debit > 0:
            balance -= line.debit
        else:
            balance += line.credit
    
    return balance


def get_month_last_day(year, month):
    """الحصول على آخر يوم في الشهر"""
    return monthrange(year, month)[1]