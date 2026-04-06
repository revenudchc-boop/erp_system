from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
    return render(request, 'login.html')


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        phone = request.POST.get('phone', '')
        
        # التحقق من تطابق كلمة المرور
        if password != password2:
            messages.error(request, 'كلمتا المرور غير متطابقتين')
            return render(request, 'register.html')
        
        # التحقق من طول كلمة المرور
        if len(password) < 6:
            messages.error(request, 'كلمة المرور يجب أن تكون 6 أحرف على الأقل')
            return render(request, 'register.html')
        
        # التحقق من وجود اسم المستخدم
        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود بالفعل، الرجاء اختيار اسم آخر')
            return render(request, 'register.html')
        
        # التحقق من وجود البريد الإلكتروني
        if User.objects.filter(email=email).exists():
            messages.error(request, 'البريد الإلكتروني موجود بالفعل')
            return render(request, 'register.html')
        
        # إنشاء المستخدم الجديد
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        messages.success(request, f'تم إنشاء الحساب بنجاح! مرحباً {first_name}، يمكنك الآن تسجيل الدخول')
        return redirect('login')
    
    return render(request, 'register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    from accounts.models import Account
    from journal.models import JournalEntry
    from currencies.models import Currency
    
    context = {
        'total_accounts': Account.objects.count(),
        'total_entries': JournalEntry.objects.count(),
        'total_currencies': Currency.objects.count(),
        'last_entries': JournalEntry.objects.all().order_by('-date')[:5],
    }
    return render(request, 'dashboard.html', context)


urlpatterns = [
    # مسار لوحة الإدارة
    path('admin/', admin.site.urls),
    
    # مسارات المصادقة
    path('', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # مسار لوحة التحكم
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # مسارات API للتطبيقات
    path('api/accounts/', include('accounts.urls')),
    path('api/journal/', include('journal.urls')),
    
    # مسارات التطبيقات (واجهات المستخدم)
    path('currencies/', include('currencies.urls')),
        
        # مسارات التطبيقات (واجهات المستخدم)
    path('customers/', include('customers.urls')),
    
            # مسارات التطبيقات (واجهات المستخدم)
    path('suppliers/', include('suppliers.urls')),
    
                # مسارات التطبيقات (واجهات المستخدم)
    path('banks/', include('banks.urls')),
    
                    # مسارات التطبيقات (واجهات المستخدم)
    path('inventory/', include('inventory.urls')),
    
                        # مسارات التطبيقات (واجهات المستخدم)
    path('cost-centers/', include('cost_centers.urls')),
    
                            # مسارات التطبيقات (واجهات المستخدم)
   path('reports/', include('reports.urls')),
   
                               # مسارات التطبيقات (واجهات المستخدم)
   path('transactions/', include('transactions.urls')),
   
                                  # مسارات التطبيقات (واجهات المستخدم)
   path('core/', include('core.urls')),

]