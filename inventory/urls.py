from django.urls import path
from . import views

urlpatterns = [
    # المستودعات
    path('warehouses/', views.warehouses_list, name='warehouses_list'),
    path('warehouses/create/', views.warehouse_create, name='warehouse_create'),
    path('warehouses/<int:id>/update/', views.warehouse_update, name='warehouse_update'),
    path('warehouses/<int:id>/delete/', views.warehouse_delete, name='warehouse_delete'),
    
    # فئات الأصناف
    path('categories/', views.categories_list, name='categories_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:id>/update/', views.category_update, name='category_update'),
    path('categories/<int:id>/delete/', views.category_delete, name='category_delete'),
    
    # السلع
    path('goods/', views.goods_list, name='goods_list'),
    path('goods/create/', views.goods_create, name='goods_create'),
    path('goods/<int:id>/update/', views.goods_update, name='goods_update'),
    path('goods/<int:id>/delete/', views.goods_delete, name='goods_delete'),
    
    # المواد الخام
    path('raw-materials/', views.raw_materials_list, name='raw_materials_list'),
    path('raw-materials/create/', views.raw_material_create, name='raw_material_create'),
    
    # المنتجات النهائية
    path('finished-goods/', views.finished_goods_list, name='finished_goods_list'),
    path('finished-goods/create/', views.finished_good_create, name='finished_good_create'),
    
    # الخدمات
    path('services/', views.services_list, name='services_list'),
    path('services/create/', views.service_create, name='service_create'),
    path('services/<int:id>/update/', views.service_update, name='service_update'),
    path('services/<int:id>/delete/', views.service_delete, name='service_delete'),
    
    # حركات المخزون
    path('transactions/', views.transactions_list, name='transactions_list'),  # <-- أضف هذا السطر
    
    # أرصدة المخزون
    path('stock-balance/', views.stock_balance, name='stock_balance'),
    
    # صرف المواد الخام
    path('raw-material-issue/', views.raw_material_issue, name='raw_material_issue'),
    path('raw-material-issues/', views.raw_material_issues_list, name='raw_material_issues_list'),
]