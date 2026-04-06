from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from .models import (
    PurchaseInvoice, PurchaseLine, PurchaseReturn, PurchaseReturnLine,
    SalesInvoice, SalesLine, SalesReturn, SalesReturnLine
)
from inventory.models import Product, Warehouse, InventoryTransaction, StockBalance
from customers.models import Customer
from suppliers.models import Supplier
from currencies.models import Currency
from accounts.models import Account
from journal.models import JournalEntry, JournalLine
from cost_centers.models import CostCenter
from core.models import CompanySettings


# ==================== المشتريات ====================

@login_required
def purchase_list(request):
    purchases = PurchaseInvoice.objects.all().order_by('-date')
    return render(request, 'transactions/purchase_list.html', {'purchases': purchases})


@login_required
def purchase_detail(request, id):
    purchase = get_object_or_404(PurchaseInvoice, id=id)
    lines = purchase.lines.all()
    return JsonResponse({
        'id': purchase.id,
        'invoice_number': purchase.invoice_number,
        'date': purchase.date.isoformat(),
        'supplier_id': purchase.supplier_id,
        'warehouse_id': purchase.warehouse_id,
        'notes': purchase.notes,
        'status': purchase.status,
        'lines': [{
            'product_id': l.product_id,
            'product_name': l.product.name_ar,
            'quantity': float(l.quantity),
            'unit_price': float(l.unit_price),
            'discount': float(l.discount),
            'vat_rate': float(l.vat_rate),
            'total': float(l.total)
        } for l in lines]
    })


@login_required
def purchase_create(request):
    company_settings = CompanySettings.objects.first()
    
    if request.method == 'POST':
        with transaction.atomic():
            # معالجة سعر الصرف
            exchange_rate = request.POST.get('exchange_rate', '1')
            if exchange_rate == '' or exchange_rate is None:
                exchange_rate = '1'
            
            invoice = PurchaseInvoice.objects.create(
                invoice_number=request.POST.get('invoice_number'),
                date=request.POST.get('date'),
                supplier_id=request.POST.get('supplier'),
                warehouse_id=request.POST.get('warehouse'),
                currency_id=request.POST.get('currency', 1),
                exchange_rate=Decimal(exchange_rate),
                notes=request.POST.get('notes', '')
            )
            
            products = request.POST.getlist('product[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')
            vat_rates = request.POST.getlist('vat_rate[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            # تحويل القيم الفارغة إلى أرقام
            quantities = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in quantities]
            unit_prices = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in unit_prices]
            discounts = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in discounts]
            vat_rates = [Decimal(str(x)) if x and x != '' else Decimal('14') for x in vat_rates]
            
            for i in range(len(products)):
                if products[i]:
                    PurchaseLine.objects.create(
                        invoice=invoice,
                        product_id=products[i],
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        discount=discounts[i],
                        vat_rate=vat_rates[i],
                        cost_center_id=cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    )
            
            messages.success(request, 'تم إضافة فاتورة المشتريات كمسودة')
            return redirect('purchase_list')
    
    suppliers = Supplier.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    
    if company_settings and company_settings.company_type == 'trading':
        products = Product.objects.filter(product_type='goods', is_active=True)
    else:
        products = Product.objects.filter(product_usage='raw_material', is_active=True)
    
    return render(request, 'transactions/purchase_form.html', {
        'suppliers': suppliers,
        'warehouses': warehouses,
        'currencies': currencies,
        'products': products,
        'cost_centers': cost_centers,
        'title': 'إضافة فاتورة مشتريات'
    })


@login_required
def purchase_update(request, id):
    purchase = get_object_or_404(PurchaseInvoice, id=id)
    company_settings = CompanySettings.objects.first()
    
    if purchase.status != 'draft':
        messages.error(request, 'لا يمكن تعديل فاتورة مرحلة')
        return redirect('purchase_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            purchase.invoice_number = request.POST.get('invoice_number')
            purchase.date = request.POST.get('date')
            purchase.supplier_id = request.POST.get('supplier')
            purchase.warehouse_id = request.POST.get('warehouse')
            purchase.currency_id = request.POST.get('currency', 1)
            exchange_rate = request.POST.get('exchange_rate', '1')
            if exchange_rate == '' or exchange_rate is None:
                exchange_rate = '1'
            exchange_rate = Decimal(exchange_rate)
            purchase.notes = request.POST.get('notes', '')
            purchase.save()
            
            purchase.lines.all().delete()
            
            products = request.POST.getlist('product[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')
            vat_rates = request.POST.getlist('vat_rate[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            discounts = [float(x) if x != '' else 0 for x in discounts]
            vat_rates = [float(x) if x != '' else 14 for x in vat_rates]
            
            for i in range(len(products)):
                if products[i]:
                    PurchaseLine.objects.create(
                        invoice=purchase,
                        product_id=products[i],
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        discount=discounts[i],
                        vat_rate=vat_rates[i],
                        cost_center_id=cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    )
            
            messages.success(request, 'تم تحديث فاتورة المشتريات')
            return redirect('purchase_list')
    
    suppliers = Supplier.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    lines = purchase.lines.all()
    
    if company_settings and company_settings.company_type == 'trading':
        products = Product.objects.filter(product_type='goods', is_active=True)
    else:
        products = Product.objects.filter(product_usage='raw_material', is_active=True)
    
    return render(request, 'transactions/purchase_form.html', {
        'purchase': purchase,
        'suppliers': suppliers,
        'warehouses': warehouses,
        'currencies': currencies,
        'products': products,
        'cost_centers': cost_centers,
        'lines': lines,
        'title': 'تعديل فاتورة مشتريات'
    })

@login_required
def purchase_delete(request, id):
    purchase = get_object_or_404(PurchaseInvoice, id=id)
    
    if purchase.status != 'draft':
        messages.error(request, 'لا يمكن حذف فاتورة مرحلة')
        return redirect('purchase_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            if purchase.journal_entry:
                purchase.journal_entry.lines.all().delete()
                purchase.journal_entry.delete()
            
            # حذف حركات المخزون المرتبطة
            InventoryTransaction.objects.filter(
                reference_type='purchase_invoice',
                reference_id=purchase.id
            ).delete()
            
            purchase.lines.all().delete()
            purchase.delete()
        
        messages.success(request, 'تم حذف فاتورة المشتريات')
        return redirect('purchase_list')
    
    return render(request, 'transactions/purchase_delete.html', {'purchase': purchase})


@login_required
def purchase_post(request, id):
    purchase = get_object_or_404(PurchaseInvoice, id=id)
    
    if purchase.status != 'draft':
        messages.warning(request, 'الفاتورة مرحلة بالفعل')
        return redirect('purchase_list')
    
    with transaction.atomic():
        total_goods = Decimal('0')
        total_vat = Decimal('0')
        
        for line in purchase.lines.all():
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            total_goods += line_total
            total_vat += vat_amount
        
        total_invoice = total_goods + total_vat
        
        inventory_account = Account.objects.filter(code='14').first()
        if not inventory_account:
            inventory_account = Account.objects.create(
                code='14',
                name='المخزون',
                type='asset',
                balance=0,
                is_active=True
            )
        
        vat_account = Account.objects.filter(code='215').first()
        if not vat_account:
            vat_account = Account.objects.create(
                code='215',
                name='ضريبة القيمة المضافة المستحقة',
                type='liability',
                balance=0,
                is_active=True
            )
        
        supplier_account = purchase.supplier.account
        
        # تحديث أرصدة الحسابات
        supplier_account.balance += total_invoice
        supplier_account.save()
        
        inventory_account.balance += total_goods
        inventory_account.save()
        
        if total_vat > 0:
            vat_account.balance += total_vat
            vat_account.save()
        
        # إنشاء القيد المحاسبي
        entry = JournalEntry.objects.create(
            date=purchase.date,
            description=f"شراء من {purchase.supplier.name} - فاتورة {purchase.invoice_number}",
            reference=purchase.invoice_number,
            is_posted=True,
            posted_at=timezone.now(),
            posted_by=request.user,
            is_adjustment=False
        )
        
        JournalLine.objects.create(
            entry=entry,
            account=supplier_account,
            debit=0,
            credit=total_invoice
        )
        
        JournalLine.objects.create(
            entry=entry,
            account=inventory_account,
            debit=total_goods,
            credit=0
        )
        
        if total_vat > 0:
            JournalLine.objects.create(
                entry=entry,
                account=vat_account,
                debit=total_vat,
                credit=0
            )
        
        # إضافة سطور مراكز التكلفة (إذا وجدت)
        for line in purchase.lines.all():
            if line.cost_center:
                # إضافة سطر قيد إضافي لمركز التكلفة (اختياري حسب احتياجك)
                # يمكن ربط cost_center بسطر المخزون أو إضافة سطر منفصل
                pass
        
        purchase.journal_entry = entry
        purchase.status = 'posted'
        purchase.save()
        
        # تحديث المخزون
        for line in purchase.lines.all():
            product = line.product
            if product.product_usage == 'raw_material' or (company_settings and company_settings.company_type == 'trading'):
                if (product.current_stock + line.quantity) > 0:
                    new_avg_cost = ((product.current_stock * product.avg_cost) + (line.quantity * line.unit_price)) / (product.current_stock + line.quantity)
                else:
                    new_avg_cost = line.unit_price
                product.avg_cost = new_avg_cost
                product.current_stock += line.quantity
                product.save()
                
                if purchase.warehouse:
                    InventoryTransaction.objects.create(
                        product=product,
                        warehouse=purchase.warehouse,
                        type='purchase_in',
                        quantity=line.quantity,
                        unit_cost=line.unit_price,
                        total_cost=line.total,
                        reference_type='purchase_invoice',
                        reference_id=purchase.id,
                        date=purchase.date
                    )
                    
                    stock_balance, created = StockBalance.objects.get_or_create(
                        product=product,
                        warehouse=purchase.warehouse,
                        defaults={'quantity': 0, 'avg_cost': 0}
                    )
                    stock_balance.quantity += line.quantity
                    stock_balance.avg_cost = product.avg_cost
                    stock_balance.save()
    
    messages.success(request, 'تم ترحيل فاتورة المشتريات')
    return redirect('purchase_list')


@login_required
def purchase_unpost(request, id):
    purchase = get_object_or_404(PurchaseInvoice, id=id)
    company_settings = CompanySettings.objects.first()
    
    if purchase.status != 'posted':
        messages.warning(request, 'الفاتورة غير مرحلة أصلاً')
        return redirect('purchase_list')
    
    with transaction.atomic():
        total_goods = Decimal('0')
        total_vat = Decimal('0')
        
        for line in purchase.lines.all():
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            total_goods += line_total
            total_vat += vat_amount
        
        total_invoice = total_goods + total_vat
        
        inventory_account = Account.objects.filter(code='14').first()
        vat_account = Account.objects.filter(code='215').first()
        supplier_account = purchase.supplier.account
        
        supplier_account.balance -= total_invoice
        supplier_account.save()
        
        if inventory_account:
            inventory_account.balance -= total_goods
            inventory_account.save()
        
        if vat_account and total_vat > 0:
            vat_account.balance -= total_vat
            vat_account.save()
        
        if purchase.journal_entry:
            purchase.journal_entry.lines.all().delete()
            purchase.journal_entry.delete()
        
        # حذف حركات المخزون المرتبطة
        InventoryTransaction.objects.filter(
            reference_type='purchase_invoice',
            reference_id=purchase.id
        ).delete()
        
        # عكس تأثير المخزون
        for line in purchase.lines.all():
            product = line.product
            if product.product_usage == 'raw_material' or (company_settings and company_settings.company_type == 'trading'):
                product.current_stock -= line.quantity
                product.save()
                
                if purchase.warehouse:
                    try:
                        stock_balance = StockBalance.objects.get(product=product, warehouse=purchase.warehouse)
                        stock_balance.quantity -= line.quantity
                        stock_balance.save()
                    except StockBalance.DoesNotExist:
                        pass
        
        purchase.status = 'draft'
        purchase.journal_entry = None
        purchase.save()
    
    messages.success(request, 'تم إلغاء ترحيل فاتورة المشتريات')
    return redirect('purchase_list')


# ==================== مردود المشتريات ====================

@login_required
def purchase_return_list(request):
    returns = PurchaseReturn.objects.all().order_by('-date')
    return render(request, 'transactions/purchase_return_list.html', {'returns': returns})


@login_required
def purchase_return_create(request):
    if request.method == 'POST':
        with transaction.atomic():
            # معالجة سعر الصرف
            exchange_rate = request.POST.get('exchange_rate', '1')
            if exchange_rate == '' or exchange_rate is None:
                exchange_rate = '1'
            
            return_inv = PurchaseReturn.objects.create(
                return_number=request.POST.get('return_number'),
                date=request.POST.get('date'),
                original_invoice_id=request.POST.get('original_invoice'),
                supplier_id=request.POST.get('supplier'),
                warehouse_id=request.POST.get('warehouse'),
                currency_id=request.POST.get('currency', 1),
                exchange_rate=Decimal(exchange_rate),
                notes=request.POST.get('notes', '')
            )
            
            products = request.POST.getlist('product[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')
            vat_rates = request.POST.getlist('vat_rate[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            # تحويل القيم الفارغة إلى أرقام
            quantities = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in quantities]
            unit_prices = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in unit_prices]
            discounts = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in discounts]
            vat_rates = [Decimal(str(x)) if x and x != '' else Decimal('14') for x in vat_rates]
            
            for i in range(len(products)):
                if products[i]:
                    PurchaseReturnLine.objects.create(
                        return_invoice=return_inv,
                        product_id=products[i],
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        discount=discounts[i],
                        vat_rate=vat_rates[i],
                        cost_center_id=cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    )
            
            messages.success(request, 'تم إضافة مردود المشتريات كمسودة')
            return redirect('purchase_return_list')
    
    suppliers = Supplier.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True, product_type='goods')
    purchase_invoices = PurchaseInvoice.objects.filter(status='posted')
    
    return render(request, 'transactions/purchase_return_form.html', {
        'suppliers': suppliers,
        'warehouses': warehouses,
        'currencies': currencies,
        'products': products,
        'cost_centers': cost_centers,
        'purchase_invoices': purchase_invoices,
        'title': 'إضافة مردود مشتريات'
    })


@login_required
def purchase_return_post(request, id):
    return_inv = get_object_or_404(PurchaseReturn, id=id)
    
    if return_inv.status != 'draft':
        messages.warning(request, 'المردود مرحل بالفعل')
        return redirect('purchase_return_list')
    
    with transaction.atomic():
        total_goods = Decimal('0')
        total_vat = Decimal('0')
        
        for line in return_inv.lines.all():
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            total_goods += line_total
            total_vat += vat_amount
        
        total_return = total_goods + total_vat
        
        inventory_account = Account.objects.filter(code='14').first()
        if not inventory_account:
            inventory_account = Account.objects.create(
                code='14',
                name='المخزون',
                type='asset',
                balance=0,
                is_active=True
            )
        
        vat_account = Account.objects.filter(code='215').first()
        if not vat_account:
            vat_account = Account.objects.create(
                code='215',
                name='ضريبة القيمة المضافة المستحقة',
                type='liability',
                balance=0,
                is_active=True
            )
        
        supplier_account = return_inv.supplier.account
        
        # تحديث أرصدة الحسابات (عكسياً)
        supplier_account.balance -= total_return
        supplier_account.save()
        
        inventory_account.balance -= total_goods
        inventory_account.save()
        
        if total_vat > 0:
            vat_account.balance -= total_vat
            vat_account.save()
        
        # إنشاء القيد المحاسبي
        entry = JournalEntry.objects.create(
            date=return_inv.date,
            description=f"مردود مشتريات من {return_inv.supplier.name} - {return_inv.return_number}",
            reference=return_inv.return_number,
            is_posted=True,
            posted_at=timezone.now(),
            posted_by=request.user,
            is_adjustment=True,
            adjustment_type='inventory'
        )
        
        JournalLine.objects.create(
            entry=entry,
            account=supplier_account,
            debit=total_return,
            credit=0
        )
        
        JournalLine.objects.create(
            entry=entry,
            account=inventory_account,
            debit=0,
            credit=total_goods
        )
        
        if total_vat > 0:
            JournalLine.objects.create(
                entry=entry,
                account=vat_account,
                debit=0,
                credit=total_vat
            )
        
        # إضافة سطور مراكز التكلفة (إذا وجدت)
        for line in return_inv.lines.all():
            if line.cost_center:
                # يمكن إضافة تأثير على مراكز التكلفة هنا إذا لزم الأمر
                pass
        
        return_inv.journal_entry = entry
        return_inv.status = 'posted'
        return_inv.save()
        
        # تحديث المخزون
        for line in return_inv.lines.all():
            product = line.product
            if product.product_type == 'goods':
                product.current_stock -= line.quantity
                product.save()
                
                if return_inv.warehouse:
                    InventoryTransaction.objects.create(
                        product=product,
                        warehouse=return_inv.warehouse,
                        type='return_out',
                        quantity=line.quantity,
                        unit_cost=line.unit_price,
                        total_cost=line.total,
                        reference_type='purchase_return',
                        reference_id=return_inv.id,
                        date=return_inv.date
                    )
                    
                    try:
                        stock_balance = StockBalance.objects.get(product=product, warehouse=return_inv.warehouse)
                        stock_balance.quantity -= line.quantity
                        stock_balance.save()
                    except StockBalance.DoesNotExist:
                        pass
    
    messages.success(request, 'تم ترحيل مردود المشتريات وإنشاء القيد المحاسبي')
    return redirect('purchase_return_list')


@login_required
def purchase_return_unpost(request, id):
    return_inv = get_object_or_404(PurchaseReturn, id=id)
    
    if return_inv.status != 'posted':
        messages.warning(request, 'المردود غير مرحل أصلاً')
        return redirect('purchase_return_list')
    
    with transaction.atomic():
        total_goods = Decimal('0')
        total_vat = Decimal('0')
        
        for line in return_inv.lines.all():
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            total_goods += line_total
            total_vat += vat_amount
        
        total_return = total_goods + total_vat
        
        inventory_account = Account.objects.filter(code='14').first()
        vat_account = Account.objects.filter(code='215').first()
        supplier_account = return_inv.supplier.account
        
        supplier_account.balance += total_return
        supplier_account.save()
        
        if inventory_account:
            inventory_account.balance += total_goods
            inventory_account.save()
        
        if vat_account and total_vat > 0:
            vat_account.balance += total_vat
            vat_account.save()
        
        if return_inv.journal_entry:
            return_inv.journal_entry.lines.all().delete()
            return_inv.journal_entry.delete()
        
        return_inv.status = 'draft'
        return_inv.journal_entry = None
        return_inv.save()
        
        for line in return_inv.lines.all():
            product = line.product
            if product.product_type == 'goods':
                product.current_stock += line.quantity
                product.save()
    
    messages.success(request, 'تم إلغاء ترحيل مردود المشتريات')
    return redirect('purchase_return_list')


@login_required
def purchase_return_delete(request, id):
    return_inv = get_object_or_404(PurchaseReturn, id=id)
    
    if return_inv.status != 'draft':
        messages.error(request, 'لا يمكن حذف مردود مرحلة')
        return redirect('purchase_return_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            if return_inv.journal_entry:
                return_inv.journal_entry.lines.all().delete()
                return_inv.journal_entry.delete()
            
            return_inv.lines.all().delete()
            return_inv.delete()
        
        messages.success(request, 'تم حذف مردود المشتريات')
        return redirect('purchase_return_list')
    
    return render(request, 'transactions/purchase_return_delete.html', {'return_inv': return_inv})
    # ==================== المبيعات ====================

@login_required
def sales_list(request):
    sales = SalesInvoice.objects.all().order_by('-date')
    return render(request, 'transactions/sales_list.html', {'sales': sales})


@login_required
def sales_detail(request, id):
    sale = get_object_or_404(SalesInvoice, id=id)
    lines = sale.lines.all()
    return JsonResponse({
        'id': sale.id,
        'invoice_number': sale.invoice_number,
        'date': sale.date.isoformat(),
        'customer_id': sale.customer_id,
        'warehouse_id': sale.warehouse_id,
        'notes': sale.notes,
        'status': sale.status,
        'lines': [{
            'product_id': l.product_id,
            'product_name': l.product.name_ar,
            'product_type': l.product.product_type,
            'quantity': float(l.quantity),
            'unit_price': float(l.unit_price),
            'discount': float(l.discount),
            'vat_rate': float(l.vat_rate),
            'total': float(l.total)
        } for l in lines]
    })


@login_required
def sales_create(request):
    company_settings = CompanySettings.objects.first()
    
    if request.method == 'POST':
        with transaction.atomic():
            # معالجة سعر الصرف
            exchange_rate = request.POST.get('exchange_rate', '1')
            if exchange_rate == '' or exchange_rate is None:
                exchange_rate = '1'
            
            invoice = SalesInvoice.objects.create(
                invoice_number=request.POST.get('invoice_number'),
                date=request.POST.get('date'),
                customer_id=request.POST.get('customer'),
                warehouse_id=request.POST.get('warehouse') or None,
                currency_id=request.POST.get('currency', 1),
                exchange_rate=Decimal(exchange_rate),
                notes=request.POST.get('notes', '')
            )
            
            products = request.POST.getlist('product[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')
            vat_rates = request.POST.getlist('vat_rate[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            # تحويل القيم الفارغة إلى أرقام
            quantities = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in quantities]
            unit_prices = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in unit_prices]
            discounts = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in discounts]
            vat_rates = [Decimal(str(x)) if x and x != '' else Decimal('14') for x in vat_rates]
            
            for i in range(len(products)):
                if products[i]:
                    SalesLine.objects.create(
                        invoice=invoice,
                        product_id=products[i],
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        discount=discounts[i],
                        vat_rate=vat_rates[i],
                        cost_center_id=cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    )
            
            messages.success(request, 'تم إضافة فاتورة المبيعات كمسودة')
            return redirect('sales_list')
    
    customers = Customer.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    
    if company_settings and company_settings.company_type == 'trading':
        products = Product.objects.filter(product_type='goods', is_active=True)
    else:
        products = Product.objects.filter(product_usage__in=['finished_good', 'service'], is_active=True)
    
    return render(request, 'transactions/sales_form.html', {
        'customers': customers,
        'warehouses': warehouses,
        'currencies': currencies,
        'products': products,
        'cost_centers': cost_centers,
        'title': 'إضافة فاتورة مبيعات'
    })


@login_required
def sales_update(request, id):
    sale = get_object_or_404(SalesInvoice, id=id)
    company_settings = CompanySettings.objects.first()
    
    if sale.status != 'draft':
        messages.error(request, 'لا يمكن تعديل فاتورة مرحلة')
        return redirect('sales_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            # معالجة سعر الصرف
            exchange_rate = request.POST.get('exchange_rate', '1')
            if exchange_rate == '' or exchange_rate is None:
                exchange_rate = '1'
            
            sale.invoice_number = request.POST.get('invoice_number')
            sale.date = request.POST.get('date')
            sale.customer_id = request.POST.get('customer')
            sale.warehouse_id = request.POST.get('warehouse') or None
            sale.currency_id = request.POST.get('currency', 1)
            sale.exchange_rate = Decimal(exchange_rate)
            sale.notes = request.POST.get('notes', '')
            sale.save()
            
            # حذف السطور القديمة
            sale.lines.all().delete()
            
            products = request.POST.getlist('product[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')
            vat_rates = request.POST.getlist('vat_rate[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            # تحويل القيم الفارغة إلى أرقام
            quantities = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in quantities]
            unit_prices = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in unit_prices]
            discounts = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in discounts]
            vat_rates = [Decimal(str(x)) if x and x != '' else Decimal('14') for x in vat_rates]
            
            for i in range(len(products)):
                if products[i]:
                    SalesLine.objects.create(
                        invoice=sale,
                        product_id=products[i],
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        discount=discounts[i],
                        vat_rate=vat_rates[i],
                        cost_center_id=cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    )
            
            messages.success(request, 'تم تحديث فاتورة المبيعات')
            return redirect('sales_list')
    
    customers = Customer.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    lines = sale.lines.all()
    
    if company_settings and company_settings.company_type == 'trading':
        products = Product.objects.filter(product_type='goods', is_active=True)
    else:
        products = Product.objects.filter(product_usage__in=['finished_good', 'service'], is_active=True)
    
    return render(request, 'transactions/sales_form.html', {
        'sale': sale,
        'customers': customers,
        'warehouses': warehouses,
        'currencies': currencies,
        'products': products,
        'cost_centers': cost_centers,
        'lines': lines,
        'title': 'تعديل فاتورة مبيعات'
    })


@login_required
def sales_delete(request, id):
    sale = get_object_or_404(SalesInvoice, id=id)
    
    if sale.status != 'draft':
        messages.error(request, 'لا يمكن حذف فاتورة مرحلة')
        return redirect('sales_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            if sale.journal_entry:
                sale.journal_entry.lines.all().delete()
                sale.journal_entry.delete()
            
            sale.lines.all().delete()
            sale.delete()
        
        messages.success(request, 'تم حذف فاتورة المبيعات')
        return redirect('sales_list')
    
    return render(request, 'transactions/sales_delete.html', {'sale': sale})


@login_required
def sales_post(request, id):
    sale = get_object_or_404(SalesInvoice, id=id)
    company_settings = CompanySettings.objects.first()
    
    if sale.status != 'draft':
        messages.warning(request, 'الفاتورة مرحلة بالفعل')
        return redirect('sales_list')
    
    with transaction.atomic():
        total_goods = Decimal('0')
        total_vat = Decimal('0')
        
        for line in sale.lines.all():
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            total_goods += line_total
            total_vat += vat_amount
        
        total_invoice = total_goods + total_vat
        
        vat_account = Account.objects.filter(code='215').first()
        if not vat_account:
            vat_account = Account.objects.create(
                code='215',
                name='ضريبة القيمة المضافة المستحقة',
                type='liability',
                balance=0,
                is_active=True
            )
        
        customer_account = sale.customer.account
        
        # تحديث رصيد العميل
        customer_account.balance += total_invoice
        customer_account.save()
        
        # تحديث رصيد ضريبة القيمة المضافة
        if total_vat > 0:
            vat_account.balance -= total_vat
            vat_account.save()
        
        # إنشاء القيد المحاسبي
        entry = JournalEntry.objects.create(
            date=sale.date,
            description=f"بيع إلى {sale.customer.name} - فاتورة {sale.invoice_number}",
            reference=sale.invoice_number,
            is_posted=True,
            posted_at=timezone.now(),
            posted_by=request.user,
            is_adjustment=False
        )
        
        # سطر مدين: العميل
        JournalLine.objects.create(
            entry=entry,
            account=customer_account,
            debit=total_invoice,
            credit=0
        )
        
        # سطر دائن: ضريبة المبيعات
        if total_vat > 0:
            JournalLine.objects.create(
                entry=entry,
                account=vat_account,
                debit=0,
                credit=total_vat
            )
        
        # معالجة كل منتج على حدة
        for line in sale.lines.all():
            product = line.product
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            net_amount = line_total - vat_amount
            
            # حساب الإيرادات
            if product.revenue_account:
                revenue_account = product.revenue_account
            else:
                revenue_account = Account.objects.filter(code='41').first()
                if not revenue_account:
                    revenue_account = Account.objects.create(
                        code='41',
                        name='إيرادات النشاط الرئيسي',
                        type='revenue',
                        balance=0,
                        is_active=True
                    )
            
            revenue_account.balance -= net_amount
            revenue_account.save()
            
            JournalLine.objects.create(
                entry=entry,
                account=revenue_account,
                debit=0,
                credit=net_amount,
                cost_center=line.cost_center
            )
            
            # معالجة تكلفة المبيعات (للتجار فقط)
            if company_settings and company_settings.company_type == 'trading':
                if product.product_type == 'goods':
                    cogs = line.quantity * product.avg_cost
                    cogs_account = product.cost_of_sales_account or Account.objects.filter(code='51').first()
                    
                    if cogs_account:
                        cogs_account.balance += cogs
                        cogs_account.save()
                        
                        JournalLine.objects.create(
                            entry=entry,
                            account=cogs_account,
                            debit=cogs,
                            credit=0
                        )
                        
                        inventory_account = product.inventory_account or Account.objects.filter(code='14').first()
                        if inventory_account:
                            inventory_account.balance -= cogs
                            inventory_account.save()
                            
                            JournalLine.objects.create(
                                entry=entry,
                                account=inventory_account,
                                debit=0,
                                credit=cogs
                            )
                    
                    product.current_stock -= line.quantity
                    product.save()
                    
                    if sale.warehouse:
                        InventoryTransaction.objects.create(
                            product=product,
                            warehouse=sale.warehouse,
                            type='sales_out',
                            quantity=line.quantity,
                            unit_cost=product.avg_cost,
                            total_cost=cogs,
                            reference_type='sales_invoice',
                            reference_id=sale.id,
                            date=sale.date
                        )
                        
                        stock_balance, created = StockBalance.objects.get_or_create(
                            product=product,
                            warehouse=sale.warehouse,
                            defaults={'quantity': 0, 'avg_cost': product.avg_cost}
                        )
                        stock_balance.quantity -= line.quantity
                        stock_balance.save()
        
        sale.journal_entry = entry
        sale.status = 'posted'
        sale.save()
    
    messages.success(request, 'تم ترحيل فاتورة المبيعات')
    return redirect('sales_list')


@login_required
def sales_unpost(request, id):
    """إلغاء ترحيل فاتورة مبيعات"""
    sale = get_object_or_404(SalesInvoice, id=id)
    
    if sale.status != 'posted':
        messages.warning(request, 'الفاتورة غير مرحلة أصلاً')
        return redirect('sales_list')
    
    with transaction.atomic():
        # عكس أرصدة الحسابات لكل منتج على حدة
        for line in sale.lines.all():
            product = line.product
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            net_amount = line_total - vat_amount
            
            # الحصول على حساب الإيرادات الخاص بالمنتج
            if product.revenue_account:
                revenue_account = product.revenue_account
                print(f"[DEBUG] باستخدام حساب الإيرادات: {revenue_account.code} - الرصيد قبل: {revenue_account.balance}")
            else:
                revenue_account = Account.objects.filter(code='41').first()
                print(f"[DEBUG] باستخدام حساب الإيرادات الافتراضي: {revenue_account.code if revenue_account else 'غير موجود'}")
            
            if revenue_account:
                revenue_account.balance += net_amount
                print(f"[DEBUG] إضافة {net_amount} إلى {revenue_account.code} - الرصيد بعد: {revenue_account.balance}")
                revenue_account.save()
        
        # حساب إجمالي المبالغ لعكس أرصدة العميل والضريبة
        total_goods = Decimal('0')
        total_vat = Decimal('0')
        
        for line in sale.lines.all():
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            total_goods += line_total
            total_vat += vat_amount
        
        total_invoice = total_goods + total_vat
        
        vat_account = Account.objects.filter(code='215').first()
        customer_account = sale.customer.account
        
        # عكس أرصدة العميل والضريبة
        customer_account.balance -= total_invoice
        customer_account.save()
        print(f"[DEBUG] عكس رصيد العميل: {customer_account.code} - الرصيد بعد: {customer_account.balance}")
        
        if vat_account and total_vat > 0:
            vat_account.balance += total_vat
            vat_account.save()
            print(f"[DEBUG] عكس رصيد الضريبة: {vat_account.code} - الرصيد بعد: {vat_account.balance}")
        
        # حذف القيد المحاسبي
        if sale.journal_entry:
            sale.journal_entry.lines.all().delete()
            sale.journal_entry.delete()
            print("[DEBUG] تم حذف القيد المحاسبي")
        
        sale.status = 'draft'
        sale.journal_entry = None
        sale.save()
    
    messages.success(request, 'تم إلغاء ترحيل فاتورة المبيعات')
    return redirect('sales_list')


# ==================== مردود المبيعات ====================

@login_required
def sales_return_list(request):
    returns = SalesReturn.objects.all().order_by('-date')
    return render(request, 'transactions/sales_return_list.html', {'returns': returns})


# ==================== مردود المبيعات ====================

@login_required
def sales_return_create(request):
    if request.method == 'POST':
        with transaction.atomic():
            # معالجة سعر الصرف
            exchange_rate = request.POST.get('exchange_rate', '1')
            if exchange_rate == '' or exchange_rate is None:
                exchange_rate = '1'
            
            return_inv = SalesReturn.objects.create(
                return_number=request.POST.get('return_number'),
                date=request.POST.get('date'),
                original_invoice_id=request.POST.get('original_invoice'),
                customer_id=request.POST.get('customer'),
                warehouse_id=request.POST.get('warehouse') or None,
                currency_id=request.POST.get('currency', 1),
                exchange_rate=Decimal(exchange_rate),
                notes=request.POST.get('notes', '')
            )
            
            products = request.POST.getlist('product[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')
            vat_rates = request.POST.getlist('vat_rate[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            # تحويل القيم الفارغة إلى أرقام
            quantities = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in quantities]
            unit_prices = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in unit_prices]
            discounts = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in discounts]
            vat_rates = [Decimal(str(x)) if x and x != '' else Decimal('14') for x in vat_rates]
            
            for i in range(len(products)):
                if products[i]:
                    SalesReturnLine.objects.create(
                        return_invoice=return_inv,
                        product_id=products[i],
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        discount=discounts[i],
                        vat_rate=vat_rates[i],
                        cost_center_id=cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    )
            
            messages.success(request, 'تم إضافة مردود المبيعات كمسودة')
            return redirect('sales_return_list')
    
    customers = Customer.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    sales_invoices = SalesInvoice.objects.filter(status='posted')
    
    return render(request, 'transactions/sales_return_form.html', {
        'customers': customers,
        'warehouses': warehouses,
        'currencies': currencies,
        'products': products,
        'cost_centers': cost_centers,
        'sales_invoices': sales_invoices,
        'title': 'إضافة مردود مبيعات'
    })


@login_required
def sales_return_post(request, id):
    return_inv = get_object_or_404(SalesReturn, id=id)
    
    if return_inv.status != 'draft':
        messages.warning(request, 'المردود مرحل بالفعل')
        return redirect('sales_return_list')
    
    with transaction.atomic():
        total_goods = Decimal('0')
        total_vat = Decimal('0')
        
        for line in return_inv.lines.all():
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            total_goods += line_total
            total_vat += vat_amount
        
        total_return = total_goods + total_vat
        
        revenue_account = Account.objects.filter(code='41').first()
        if not revenue_account:
            revenue_account = Account.objects.create(
                code='41',
                name='إيرادات النشاط الرئيسي',
                type='revenue',
                balance=0,
                is_active=True
            )
        
        vat_account = Account.objects.filter(code='215').first()
        if not vat_account:
            vat_account = Account.objects.create(
                code='215',
                name='ضريبة القيمة المضافة المستحقة',
                type='liability',
                balance=0,
                is_active=True
            )
        
        customer_account = return_inv.customer.account
        
        # تحديث أرصدة الحسابات (عكسياً)
        customer_account.balance -= total_return
        customer_account.save()
        
        revenue_account.balance += total_goods
        revenue_account.save()
        
        if total_vat > 0:
            vat_account.balance += total_vat
            vat_account.save()
        
        # إنشاء القيد المحاسبي
        entry = JournalEntry.objects.create(
            date=return_inv.date,
            description=f"مردود مبيعات من {return_inv.customer.name} - {return_inv.return_number}",
            reference=return_inv.return_number,
            is_posted=True,
            posted_at=timezone.now(),
            posted_by=request.user,
            is_adjustment=True,
            adjustment_type='inventory'
        )
        
        JournalLine.objects.create(
            entry=entry,
            account=customer_account,
            debit=0,
            credit=total_return
        )
        
        JournalLine.objects.create(
            entry=entry,
            account=revenue_account,
            debit=total_goods,
            credit=0
        )
        
        if total_vat > 0:
            JournalLine.objects.create(
                entry=entry,
                account=vat_account,
                debit=total_vat,
                credit=0
            )
        
        # إضافة سطور مراكز التكلفة (إذا وجدت)
        for line in return_inv.lines.all():
            if line.cost_center:
                # يمكن إضافة تأثير على مراكز التكلفة هنا
                pass
        
        return_inv.journal_entry = entry
        return_inv.status = 'posted'
        return_inv.save()
        
        # تحديث المخزون (للسلع فقط)
        for line in return_inv.lines.all():
            product = line.product
            if product.product_type == 'goods':
                product.current_stock += line.quantity
                product.save()
                
                if return_inv.warehouse:
                    InventoryTransaction.objects.create(
                        product=product,
                        warehouse=return_inv.warehouse,
                        type='return_in',
                        quantity=line.quantity,
                        unit_cost=line.unit_price,
                        total_cost=line.total,
                        reference_type='sales_return',
                        reference_id=return_inv.id,
                        date=return_inv.date
                    )
                    
                    stock_balance, created = StockBalance.objects.get_or_create(
                        product=product,
                        warehouse=return_inv.warehouse,
                        defaults={'quantity': 0, 'avg_cost': product.avg_cost}
                    )
                    stock_balance.quantity += line.quantity
                    stock_balance.save()
    
    messages.success(request, 'تم ترحيل مردود المبيعات وإنشاء القيد المحاسبي')
    return redirect('sales_return_list')


@login_required
def sales_return_unpost(request, id):
    """إلغاء ترحيل مردود مبيعات"""
    return_inv = get_object_or_404(SalesReturn, id=id)
    
    if return_inv.status != 'posted':
        messages.warning(request, 'المردود غير مرحل أصلاً')
        return redirect('sales_return_list')
    
    with transaction.atomic():
        total_goods = Decimal('0')
        total_vat = Decimal('0')
        
        for line in return_inv.lines.all():
            line_total = line.total
            vat_amount = line_total * line.vat_rate / Decimal('100')
            total_goods += line_total
            total_vat += vat_amount
        
        total_return = total_goods + total_vat
        
        revenue_account = Account.objects.filter(code='41').first()
        vat_account = Account.objects.filter(code='215').first()
        customer_account = return_inv.customer.account
        
        customer_account.balance += total_return
        customer_account.save()
        
        if revenue_account:
            revenue_account.balance -= total_goods
            revenue_account.save()
        
        if vat_account and total_vat > 0:
            vat_account.balance -= total_vat
            vat_account.save()
        
        if return_inv.journal_entry:
            return_inv.journal_entry.lines.all().delete()
            return_inv.journal_entry.delete()
        
        return_inv.status = 'draft'
        return_inv.journal_entry = None
        return_inv.save()
        
        for line in return_inv.lines.all():
            product = line.product
            if product.product_type == 'goods':
                product.current_stock -= line.quantity
                product.save()
    
    messages.success(request, 'تم إلغاء ترحيل مردود المبيعات')
    return redirect('sales_return_list')


@login_required
def sales_return_delete(request, id):
    return_inv = get_object_or_404(SalesReturn, id=id)
    
    if return_inv.status != 'draft':
        messages.error(request, 'لا يمكن حذف مردود مرحلة')
        return redirect('sales_return_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            if return_inv.journal_entry:
                return_inv.journal_entry.lines.all().delete()
                return_inv.journal_entry.delete()
            
            return_inv.lines.all().delete()
            return_inv.delete()
        
        messages.success(request, 'تم حذف مردود المبيعات')
        return redirect('sales_return_list')
    
    return render(request, 'transactions/sales_return_delete.html', {'return_inv': return_inv})
    
# ==================== تحديث مردود المبيعات ====================

@login_required
def sales_return_update(request, id):
    return_inv = get_object_or_404(SalesReturn, id=id)
    
    if return_inv.status != 'draft':
        messages.error(request, 'لا يمكن تعديل مردود مرحل')
        return redirect('sales_return_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            # معالجة سعر الصرف
            exchange_rate = request.POST.get('exchange_rate', '1')
            if exchange_rate == '' or exchange_rate is None:
                exchange_rate = '1'
            
            return_inv.return_number = request.POST.get('return_number')
            return_inv.date = request.POST.get('date')
            return_inv.original_invoice_id = request.POST.get('original_invoice')
            return_inv.customer_id = request.POST.get('customer')
            return_inv.warehouse_id = request.POST.get('warehouse') or None
            return_inv.currency_id = request.POST.get('currency', 1)
            return_inv.exchange_rate = Decimal(exchange_rate)
            return_inv.notes = request.POST.get('notes', '')
            return_inv.save()
            
            # حذف السطور القديمة
            return_inv.lines.all().delete()
            
            products = request.POST.getlist('product[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')
            vat_rates = request.POST.getlist('vat_rate[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            # تحويل القيم الفارغة إلى أرقام
            quantities = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in quantities]
            unit_prices = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in unit_prices]
            discounts = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in discounts]
            vat_rates = [Decimal(str(x)) if x and x != '' else Decimal('14') for x in vat_rates]
            
            for i in range(len(products)):
                if products[i]:
                    SalesReturnLine.objects.create(
                        return_invoice=return_inv,
                        product_id=products[i],
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        discount=discounts[i],
                        vat_rate=vat_rates[i],
                        cost_center_id=cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    )
            
            messages.success(request, 'تم تحديث مردود المبيعات')
            return redirect('sales_return_list')
    
    customers = Customer.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True)
    sales_invoices = SalesInvoice.objects.filter(status='posted')
    lines = return_inv.lines.all()
    
    return render(request, 'transactions/sales_return_form.html', {
        'return_inv': return_inv,
        'customers': customers,
        'warehouses': warehouses,
        'currencies': currencies,
        'products': products,
        'cost_centers': cost_centers,
        'sales_invoices': sales_invoices,
        'lines': lines,
        'title': 'تعديل مردود مبيعات'
    })


# ==================== تحديث مردود المشتريات ====================

@login_required
def purchase_return_update(request, id):
    return_inv = get_object_or_404(PurchaseReturn, id=id)
    
    if return_inv.status != 'draft':
        messages.error(request, 'لا يمكن تعديل مردود مرحل')
        return redirect('purchase_return_list')
    
    if request.method == 'POST':
        with transaction.atomic():
            # معالجة سعر الصرف
            exchange_rate = request.POST.get('exchange_rate', '1')
            if exchange_rate == '' or exchange_rate is None:
                exchange_rate = '1'
            
            return_inv.return_number = request.POST.get('return_number')
            return_inv.date = request.POST.get('date')
            return_inv.original_invoice_id = request.POST.get('original_invoice')
            return_inv.supplier_id = request.POST.get('supplier')
            return_inv.warehouse_id = request.POST.get('warehouse')
            return_inv.currency_id = request.POST.get('currency', 1)
            return_inv.exchange_rate = Decimal(exchange_rate)
            return_inv.notes = request.POST.get('notes', '')
            return_inv.save()
            
            # حذف السطور القديمة
            return_inv.lines.all().delete()
            
            products = request.POST.getlist('product[]')
            quantities = request.POST.getlist('quantity[]')
            unit_prices = request.POST.getlist('unit_price[]')
            discounts = request.POST.getlist('discount[]')
            vat_rates = request.POST.getlist('vat_rate[]')
            cost_centers = request.POST.getlist('cost_center[]')
            
            # تحويل القيم الفارغة إلى أرقام
            quantities = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in quantities]
            unit_prices = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in unit_prices]
            discounts = [Decimal(str(x)) if x and x != '' else Decimal('0') for x in discounts]
            vat_rates = [Decimal(str(x)) if x and x != '' else Decimal('14') for x in vat_rates]
            
            for i in range(len(products)):
                if products[i]:
                    PurchaseReturnLine.objects.create(
                        return_invoice=return_inv,
                        product_id=products[i],
                        quantity=quantities[i],
                        unit_price=unit_prices[i],
                        discount=discounts[i],
                        vat_rate=vat_rates[i],
                        cost_center_id=cost_centers[i] if i < len(cost_centers) and cost_centers[i] else None
                    )
            
            messages.success(request, 'تم تحديث مردود المشتريات')
            return redirect('purchase_return_list')
    
    suppliers = Supplier.objects.filter(is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    currencies = Currency.objects.filter(is_active=True)
    cost_centers = CostCenter.objects.filter(is_active=True)
    products = Product.objects.filter(is_active=True, product_type='goods')
    purchase_invoices = PurchaseInvoice.objects.filter(status='posted')
    lines = return_inv.lines.all()
    
    return render(request, 'transactions/purchase_return_form.html', {
        'return_inv': return_inv,
        'suppliers': suppliers,
        'warehouses': warehouses,
        'currencies': currencies,
        'products': products,
        'cost_centers': cost_centers,
        'purchase_invoices': purchase_invoices,
        'lines': lines,
        'title': 'تعديل مردود مشتريات'
    })