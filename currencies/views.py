from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Currency, ExchangeRateHistory
from datetime import date

# ==================== العملات ====================

@login_required
def currencies_list(request):
    currencies = Currency.objects.all()
    return render(request, 'currencies/list.html', {'currencies': currencies})

@login_required
def currencies_create(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        name_ar = request.POST.get('name_ar')
        name_en = request.POST.get('name_en', '')
        symbol = request.POST.get('symbol', '')
        is_base = request.POST.get('is_base') == 'on'
        exchange_rate = request.POST.get('exchange_rate', 1.0)
        decimal_places = request.POST.get('decimal_places', 2)
        
        # إذا كانت العملة أساسية، جعل جميع العملات الأخرى غير أساسية
        if is_base:
            Currency.objects.update(is_base=False)
        
        Currency.objects.create(
            code=code.upper(),
            name_ar=name_ar,
            name_en=name_en,
            symbol=symbol,
            is_base=is_base,
            exchange_rate=exchange_rate,
            decimal_places=decimal_places
        )
        
        messages.success(request, 'تم إضافة العملة بنجاح')
        return redirect('currencies_list')
    
    return render(request, 'currencies/form.html', {'title': 'إضافة عملة جديدة'})

@login_required
def currencies_update(request, id):
    currency = get_object_or_404(Currency, id=id)
    
    if request.method == 'POST':
        currency.code = request.POST.get('code').upper()
        currency.name_ar = request.POST.get('name_ar')
        currency.name_en = request.POST.get('name_en', '')
        currency.symbol = request.POST.get('symbol', '')
        is_base = request.POST.get('is_base') == 'on'
        
        if is_base and not currency.is_base:
            Currency.objects.update(is_base=False)
            currency.is_base = True
        else:
            currency.is_base = is_base
        
        currency.exchange_rate = request.POST.get('exchange_rate', 1.0)
        currency.decimal_places = request.POST.get('decimal_places', 2)
        currency.save()
        
        messages.success(request, 'تم تحديث العملة بنجاح')
        return redirect('currencies_list')
    
    return render(request, 'currencies/form.html', {'currency': currency, 'title': 'تعديل عملة'})

@login_required
def currencies_delete(request, id):
    currency = get_object_or_404(Currency, id=id)
    if currency.is_base:
        messages.error(request, 'لا يمكن حذف العملة الأساسية')
        return redirect('currencies_list')
    
    if request.method == 'POST':
        currency.delete()
        messages.success(request, 'تم حذف العملة بنجاح')
        return redirect('currencies_list')
    
    return render(request, 'currencies/delete.html', {'currency': currency})

# ==================== أسعار الصرف ====================

@login_required
def exchange_rates(request):
    currencies = Currency.objects.filter(is_base=False, is_active=True)
    return render(request, 'currencies/rates.html', {'currencies': currencies})

@login_required
def update_exchange_rate(request):
    if request.method == 'POST':
        currency_id = request.POST.get('currency_id')
        rate = request.POST.get('rate')
        currency = get_object_or_404(Currency, id=currency_id)
        
        # حفظ السعر القديم في السجل
        ExchangeRateHistory.objects.create(
            currency=currency,
            rate=currency.exchange_rate,
            date=date.today()
        )
        
        # تحديث السعر الحالي
        currency.exchange_rate = rate
        currency.save()
        
        messages.success(request, f'تم تحديث سعر {currency.code} بنجاح')
        return redirect('exchange_rates')
    
    return redirect('exchange_rates')

# ==================== API - جلب سعر الصرف ====================

@login_required
def get_exchange_rate(request, code):
    """API: جلب سعر صرف عملة معينة"""
    try:
        currency = Currency.objects.get(code=code.upper())
        return JsonResponse({
            'code': currency.code,
            'rate': float(currency.exchange_rate),
            'is_base': currency.is_base
        })
    except Currency.DoesNotExist:
        return JsonResponse({'error': 'Currency not found'}, status=404)