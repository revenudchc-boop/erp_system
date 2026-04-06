from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import CompanySettings

@login_required
def company_settings(request):
    settings_obj, created = CompanySettings.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        settings_obj.company_type = request.POST.get('company_type')
        settings_obj.company_name = request.POST.get('company_name')
        settings_obj.tax_number = request.POST.get('tax_number')
        settings_obj.updated_by = request.user
        settings_obj.save()
        
        # تحديث إعدادات Django
        settings.COMPANY_TYPE = settings_obj.company_type
        
        messages.success(request, 'تم حفظ إعدادات الشركة بنجاح')
        return redirect('company_settings')
    
    return render(request, 'core/settings.html', {'settings': settings_obj})