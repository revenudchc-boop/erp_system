from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from decimal import Decimal
from .models import Warehouse, ProductCategory, Product, InventoryTransaction, StockBalance
from accounts.models import Account
from core.models import CompanySettings


# ==================== المستودعات ====================

@login_required
def warehouses_list(request):
    warehouses = Warehouse.objects.all()
    return render(request, 'inventory/warehouses_list.html', {'warehouses': warehouses})


@login_required
def warehouse_create(request):
    if request.method == 'POST':
        warehouse = Warehouse(
            code=request.POST.get('code'),
            name=request.POST.get('name'),
            address=request.POST.get('address', '')
        )
        warehouse.save()
        messages.success(request, 'تم إضافة المستودع بنجاح')
        return redirect('warehouses_list')
    
    return render(request, 'inventory/warehouse_form.html', {'title': 'إضافة مستودع جديد'})


@login_required
def warehouse_update(request, id):
    warehouse = get_object_or_404(Warehouse, id=id)
    
    if request.method == 'POST':
        warehouse.code = request.POST.get('code')
        warehouse.name = request.POST.get('name')
        warehouse.address = request.POST.get('address', '')
        warehouse.save()
        messages.success(request, 'تم تحديث المستودع بنجاح')
        return redirect('warehouses_list')
    
    return render(request, 'inventory/warehouse_form.html', {'warehouse': warehouse, 'title': 'تعديل مستودع'})


@login_required
def warehouse_delete(request, id):
    warehouse = get_object_or_404(Warehouse, id=id)
    
    if request.method == 'POST':
        warehouse.delete()
        messages.success(request, 'تم حذف المستودع بنجاح')
        return redirect('warehouses_list')
    
    return render(request, 'inventory/warehouse_delete.html', {'warehouse': warehouse})


# ==================== فئات الأصناف ====================

@login_required
def categories_list(request):
    categories = ProductCategory.objects.filter(parent__isnull=True)
    return render(request, 'inventory/categories_list.html', {'categories': categories})


@login_required
def category_create(request):
    if request.method == 'POST':
        category = ProductCategory(
            code=request.POST.get('code'),
            name=request.POST.get('name'),
            parent_id=request.POST.get('parent') or None
        )
        category.save()
        messages.success(request, 'تم إضافة الفئة بنجاح')
        return redirect('categories_list')
    
    parents = ProductCategory.objects.all()
    return render(request, 'inventory/category_form.html', {'parents': parents, 'title': 'إضافة فئة جديدة'})


@login_required
def category_update(request, id):
    category = get_object_or_404(ProductCategory, id=id)
    
    if request.method == 'POST':
        category.code = request.POST.get('code')
        category.name = request.POST.get('name')
        category.parent_id = request.POST.get('parent') or None
        category.save()
        messages.success(request, 'تم تحديث الفئة بنجاح')
        return redirect('categories_list')
    
    parents = ProductCategory.objects.exclude(id=id)
    return render(request, 'inventory/category_form.html', {'category': category, 'parents': parents, 'title': 'تعديل فئة'})


@login_required
def category_delete(request, id):
    category = get_object_or_404(ProductCategory, id=id)
    
    if request.method == 'POST':
        if category.products.exists():
            messages.error(request, 'لا يمكن حذف فئة تحتوي على منتجات')
            return redirect('categories_list')
        category.delete()
        messages.success(request, 'تم حذف الفئة بنجاح')
        return redirect('categories_list')
    
    return render(request, 'inventory/category_delete.html', {'category': category})


# ==================== المواد الخام (للتجاري والصناعي) ====================

@login_required
def raw_materials_list(request):
    """عرض المواد الخام (تظهر في المشتريات فقط)"""
    company_settings = CompanySettings.objects.first()
    if company_settings and company_settings.company_type == 'trading':
        # شركة تجارية: المواد الخام = جميع السلع
        products = Product.objects.filter(product_type='goods', is_active=True)
    else:
        # شركة صناعية: المواد الخام فقط
        products = Product.objects.filter(product_usage='raw_material', is_active=True)
    return render(request, 'inventory/raw_materials_list.html', {'products': products})


@login_required
def raw_material_create(request):
    """إضافة مادة خام جديدة"""
    if request.method == 'POST':
        code = request.POST.get('code')
        
        # التحقق من وجود المنتج بنفس الكود
        if Product.objects.filter(code=code).exists():
            messages.error(request, f'المادة الخام بالكود {code} موجودة بالفعل')
            return redirect('raw_material_create')
        
        with transaction.atomic():
            # البحث عن حساب المخزون
            inventory_account = Account.objects.filter(code=code).first()
            if not inventory_account:
                inventory_account = Account.objects.create(
                    code=code,
                    name=f"مخزون - {request.POST.get('name_ar')}",
                    type='asset',
                    balance=0,
                    is_active=True
                )
            
            product = Product(
                product_type='goods',
                product_usage='raw_material',
                code=code,
                barcode=request.POST.get('barcode', ''),
                name_ar=request.POST.get('name_ar'),
                name_en=request.POST.get('name_en', ''),
                category_id=request.POST.get('category') or None,
                unit=request.POST.get('unit', 'قطعة'),
                valuation_method=request.POST.get('valuation_method', 'weighted_average'),
                purchase_price=request.POST.get('purchase_price', 0),
                selling_price=0,
                min_stock=request.POST.get('min_stock', 0),
                max_stock=request.POST.get('max_stock', 0),
                inventory_account=inventory_account,
                vat_rate=request.POST.get('vat_rate', 14),
                notes=request.POST.get('notes', '')
            )
            product.save()
            
            messages.success(request, 'تم إضافة المادة الخام بنجاح')
            return redirect('raw_materials_list')
    
    categories = ProductCategory.objects.filter(is_active=True)
    return render(request, 'inventory/raw_material_form.html', {
        'categories': categories,
        'title': 'إضافة مادة خام جديدة'
    })


# ==================== المنتجات النهائية (للشركات الصناعية) ====================

@login_required
def finished_goods_list(request):
    """المنتجات النهائية (تظهر في المبيعات فقط)"""
    products = Product.objects.filter(product_usage='finished_good', is_active=True)
    return render(request, 'inventory/finished_goods_list.html', {'products': products})


@login_required
def finished_good_create(request):
    """إضافة منتج نهائي جديد"""
    if request.method == 'POST':
        product = Product(
            product_type='goods',
            product_usage='finished_good',
            code=request.POST.get('code'),
            barcode=request.POST.get('barcode', ''),
            name_ar=request.POST.get('name_ar'),
            name_en=request.POST.get('name_en', ''),
            category_id=request.POST.get('category') or None,
            unit=request.POST.get('unit', 'قطعة'),
            selling_price=request.POST.get('selling_price', 0),
            revenue_account_id=request.POST.get('revenue_account') or None,
            vat_rate=request.POST.get('vat_rate', 14),
            notes=request.POST.get('notes', '')
        )
        product.save()
        
        messages.success(request, 'تم إضافة المنتج النهائي بنجاح')
        return redirect('finished_goods_list')
    
    categories = ProductCategory.objects.filter(is_active=True)
    revenue_accounts = Account.objects.filter(type='revenue', is_active=True)
    return render(request, 'inventory/finished_good_form.html', {
        'categories': categories,
        'revenue_accounts': revenue_accounts,
        'title': 'إضافة منتج نهائي جديد'
    })


# ==================== الخدمات ====================

@login_required
def services_list(request):
    services = Product.objects.filter(product_usage='service', is_active=True)
    return render(request, 'inventory/services_list.html', {'services': services})


@login_required
def service_create(request):
    if request.method == 'POST':
        product = Product(
            product_type='service',
            product_usage='service',
            code=request.POST.get('code'),
            name_ar=request.POST.get('name_ar'),
            name_en=request.POST.get('name_en', ''),
            unit=request.POST.get('unit', 'خدمة'),
            selling_price=request.POST.get('selling_price', 0),
            revenue_account_id=request.POST.get('revenue_account') or None,
            vat_rate=request.POST.get('vat_rate', 14),
            notes=request.POST.get('notes', ''),
            is_active=True
        )
        product.save()
        
        messages.success(request, 'تم إضافة الخدمة بنجاح')
        return redirect('services_list')
    
    revenue_accounts = Account.objects.filter(type='revenue', is_active=True)
    return render(request, 'inventory/service_form.html', {
        'revenue_accounts': revenue_accounts,
        'title': 'إضافة خدمة جديدة'
    })


@login_required
def service_update(request, id):
    service = get_object_or_404(Product, id=id, product_usage='service')
    
    if request.method == 'POST':
        service.code = request.POST.get('code')
        service.name_ar = request.POST.get('name_ar')
        service.name_en = request.POST.get('name_en', '')
        service.unit = request.POST.get('unit', 'خدمة')
        service.selling_price = request.POST.get('selling_price', 0)
        service.revenue_account_id = request.POST.get('revenue_account') or None
        service.vat_rate = request.POST.get('vat_rate', 14)
        service.notes = request.POST.get('notes', '')
        service.save()
        
        messages.success(request, 'تم تحديث الخدمة بنجاح')
        return redirect('services_list')
    
    revenue_accounts = Account.objects.filter(type='revenue', is_active=True)
    return render(request, 'inventory/service_form.html', {
        'service': service,
        'revenue_accounts': revenue_accounts,
        'title': 'تعديل خدمة'
    })


@login_required
def service_delete(request, id):
    service = get_object_or_404(Product, id=id, product_usage='service')
    
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'تم حذف الخدمة بنجاح')
        return redirect('services_list')
    
    return render(request, 'inventory/service_delete.html', {'service': service})


# ==================== أرصدة المخزون ====================

@login_required
def stock_balance(request):
    balances = StockBalance.objects.select_related('product', 'warehouse').all()
    return render(request, 'inventory/stock_balance.html', {'balances': balances})


# ==================== حركات المخزون ====================

@login_required
def transactions_list(request):
    transactions = InventoryTransaction.objects.all().order_by('-date')[:100]
    return render(request, 'inventory/transactions_list.html', {'transactions': transactions})


# ==================== صرف المواد الخام (للاستخدام الداخلي) ====================

@login_required
def raw_material_issue(request):
    """صرف مواد خام للإنتاج (للكشركات الصناعية فقط)"""
    if request.method == 'POST':
        with transaction.atomic():
            product = get_object_or_404(Product, id=request.POST.get('product'))
            quantity = Decimal(request.POST.get('quantity'))
            warehouse_id = request.POST.get('warehouse')
            cost_center_id = request.POST.get('cost_center')
            notes = request.POST.get('notes', '')
            
            # حساب تكلفة الصرف
            issue_cost = quantity * product.avg_cost
            
            # تحديث المخزون
            product.current_stock -= quantity
            product.save()
            
            # إنشاء حركة مخزون
            InventoryTransaction.objects.create(
                product=product,
                warehouse_id=warehouse_id,
                type='issue_out',
                quantity=quantity,
                unit_cost=product.avg_cost,
                total_cost=issue_cost,
                reference_type='material_issue',
                date=request.POST.get('date'),
                notes=notes
            )
            
            # تحديث رصيد المستودع
            stock_balance, created = StockBalance.objects.get_or_create(
                product=product,
                warehouse_id=warehouse_id,
                defaults={'quantity': 0, 'avg_cost': 0}
            )
            stock_balance.quantity -= quantity
            stock_balance.save()
            
            # إنشاء قيد محاسبي (مدين: تكلفة الإنتاج، دائن: المخزون)
            # يمكن إضافة قيد محاسبي هنا
            
            messages.success(request, 'تم صرف المواد الخام بنجاح')
            return redirect('raw_material_issues')
    
    raw_materials = Product.objects.filter(product_usage='raw_material', is_active=True)
    warehouses = Warehouse.objects.filter(is_active=True)
    from cost_centers.models import CostCenter
    cost_centers = CostCenter.objects.filter(is_active=True)
    
    return render(request, 'inventory/raw_material_issue.html', {
        'raw_materials': raw_materials,
        'warehouses': warehouses,
        'cost_centers': cost_centers
    })


@login_required
def raw_material_issues_list(request):
    """عرض حركات صرف المواد الخام"""
    issues = InventoryTransaction.objects.filter(type='issue_out').order_by('-date')
    return render(request, 'inventory/raw_material_issues_list.html', {'issues': issues})
    
# ==================== السلع (للتجار) ====================

@login_required
def goods_list(request):
    """عرض السلع - للشركات التجارية"""
    company_settings = CompanySettings.objects.first()
    if company_settings and company_settings.company_type == 'trading':
        products = Product.objects.filter(product_type='goods', is_active=True)
    else:
        products = Product.objects.filter(product_usage='raw_material', is_active=True)
    return render(request, 'inventory/goods_list.html', {'products': products})


@login_required
def goods_create(request):
    """إضافة سلعة جديدة"""
    company_settings = CompanySettings.objects.first()
    
    if request.method == 'POST':
        code = request.POST.get('code')
        
        # التحقق من وجود المنتج بنفس الكود
        if Product.objects.filter(code=code).exists():
            messages.error(request, f'المنتج بالكود {code} موجود بالفعل')
            return redirect('goods_create')
        
        with transaction.atomic():
            # تحديد الاستخدام المناسب حسب نوع الشركة
            if company_settings and company_settings.company_type == 'trading':
                # شركة تجارية: السلع تباع مباشرة
                product_usage = 'finished_good'
            else:
                # شركة صناعية: السلع هي مواد خام
                product_usage = 'raw_material'
            
            # البحث عن حساب المخزون إن وجد، أو إنشاؤه إذا لم يكن موجوداً
            inventory_account = Account.objects.filter(code=code).first()
            if not inventory_account:
                inventory_account = Account.objects.create(
                    code=code,
                    name=f"مخزون - {request.POST.get('name_ar')}",
                    type='asset',
                    balance=0,
                    is_active=True
                )
            
            # البحث عن حساب تكلفة المبيعات (للتجار فقط، ولكن ننشئه للجميع)
            cogs_code = f"COGS-{code}"
            cogs_account = Account.objects.filter(code=cogs_code).first()
            if not cogs_account:
                cogs_account = Account.objects.create(
                    code=cogs_code,
                    name=f"تكلفة مبيعات - {request.POST.get('name_ar')}",
                    type='cost_of_sales',
                    balance=0,
                    is_active=True
                )
            
            product = Product(
                product_type='goods',
                product_usage=product_usage,
                code=code,
                barcode=request.POST.get('barcode', ''),
                name_ar=request.POST.get('name_ar'),
                name_en=request.POST.get('name_en', ''),
                category_id=request.POST.get('category') or None,
                unit=request.POST.get('unit', 'قطعة'),
                valuation_method=request.POST.get('valuation_method', 'weighted_average'),
                purchase_price=request.POST.get('purchase_price', 0),
                selling_price=request.POST.get('selling_price', 0),
                min_stock=request.POST.get('min_stock', 0),
                max_stock=request.POST.get('max_stock', 0),
                inventory_account=inventory_account,
                cost_of_sales_account=cogs_account,
                revenue_account_id=request.POST.get('revenue_account') or None,
                vat_rate=request.POST.get('vat_rate', 14),
                notes=request.POST.get('notes', '')
            )
            product.save()
            
            messages.success(request, f'تم إضافة {"المادة الخام" if product_usage == "raw_material" else "السلعة"} بنجاح')
            return redirect('goods_list')
    
    categories = ProductCategory.objects.filter(is_active=True)
    revenue_accounts = Account.objects.filter(type='revenue', is_active=True)
    return render(request, 'inventory/goods_form.html', {
        'categories': categories,
        'revenue_accounts': revenue_accounts,
        'title': 'إضافة سلعة جديدة'
    })


@login_required
def goods_update(request, id):
    """تعديل سلعة"""
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        product.code = request.POST.get('code')
        product.barcode = request.POST.get('barcode', '')
        product.name_ar = request.POST.get('name_ar')
        product.name_en = request.POST.get('name_en', '')
        product.category_id = request.POST.get('category') or None
        product.unit = request.POST.get('unit', 'قطعة')
        product.valuation_method = request.POST.get('valuation_method', 'weighted_average')
        product.purchase_price = request.POST.get('purchase_price', 0)
        product.selling_price = request.POST.get('selling_price', 0)
        product.min_stock = request.POST.get('min_stock', 0)
        product.max_stock = request.POST.get('max_stock', 0)
        product.revenue_account_id = request.POST.get('revenue_account') or None
        product.vat_rate = request.POST.get('vat_rate', 14)
        product.notes = request.POST.get('notes', '')
        product.save()
        
        messages.success(request, 'تم تحديث السلعة بنجاح')
        return redirect('goods_list')
    
    categories = ProductCategory.objects.filter(is_active=True)
    revenue_accounts = Account.objects.filter(type='revenue', is_active=True)
    return render(request, 'inventory/goods_form.html', {
        'product': product,
        'categories': categories,
        'revenue_accounts': revenue_accounts,
        'title': 'تعديل سلعة'
    })


@login_required
def goods_delete(request, id):
    """حذف سلعة"""
    product = get_object_or_404(Product, id=id)
    
    if request.method == 'POST':
        if product.current_stock > 0:
            messages.error(request, f'لا يمكن حذف سلعة لديه رصيد ({product.current_stock})')
            return redirect('goods_list')
        
        try:
            # حذف حركات المخزون المرتبطة
            InventoryTransaction.objects.filter(product=product).delete()
            StockBalance.objects.filter(product=product).delete()
            
            inventory_account = product.inventory_account
            cogs_account = product.cost_of_sales_account
            
            product.delete()
            
            if inventory_account:
                try:
                    inventory_account.delete()
                except:
                    pass
            if cogs_account:
                try:
                    cogs_account.delete()
                except:
                    pass
            
            messages.success(request, 'تم حذف السلعة بنجاح')
        except Exception as e:
            messages.error(request, f'حدث خطأ أثناء الحذف: {str(e)}')
        
        return redirect('goods_list')
    
    return render(request, 'inventory/goods_delete.html', {'product': product})