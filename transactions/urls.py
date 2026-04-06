from django.urls import path
from . import views

urlpatterns = [
    # ==================== المشتريات ====================
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/create/', views.purchase_create, name='purchase_create'),
    path('purchases/<int:id>/', views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:id>/update/', views.purchase_update, name='purchase_update'),
    path('purchases/<int:id>/delete/', views.purchase_delete, name='purchase_delete'),
    path('purchases/<int:id>/post/', views.purchase_post, name='purchase_post'),
    path('purchases/<int:id>/unpost/', views.purchase_unpost, name='purchase_unpost'),  # <-- أضف هذا
    
    # ==================== مردود المشتريات ====================
    path('purchase-returns/', views.purchase_return_list, name='purchase_return_list'),
    path('purchase-returns/create/', views.purchase_return_create, name='purchase_return_create'),
    path('purchase-returns/<int:id>/post/', views.purchase_return_post, name='purchase_return_post'),
    path('purchase-returns/<int:id>/delete/', views.purchase_return_delete, name='purchase_return_delete'),
    path('purchase-returns/<int:id>/unpost/', views.purchase_return_unpost, name='purchase_return_unpost'),  # <-- أضف هذا
    path('purchase-returns/<int:id>/update/', views.purchase_return_update, name='purchase_return_update'),

    
    # ==================== المبيعات ====================
    path('sales/', views.sales_list, name='sales_list'),
    path('sales/create/', views.sales_create, name='sales_create'),
    path('sales/<int:id>/', views.sales_detail, name='sales_detail'),
    path('sales/<int:id>/update/', views.sales_update, name='sales_update'),
    path('sales/<int:id>/delete/', views.sales_delete, name='sales_delete'),
    path('sales/<int:id>/post/', views.sales_post, name='sales_post'),
    path('sales/<int:id>/unpost/', views.sales_unpost, name='sales_unpost'),
    
    # ==================== مردود المبيعات ====================
    path('sales-returns/', views.sales_return_list, name='sales_return_list'),
    path('sales-returns/create/', views.sales_return_create, name='sales_return_create'),
    path('sales-returns/<int:id>/post/', views.sales_return_post, name='sales_return_post'),
    path('sales-returns/<int:id>/delete/', views.sales_return_delete, name='sales_return_delete'),
    path('sales-returns/<int:id>/unpost/', views.sales_return_unpost, name='sales_return_unpost'),  # <-- أضف هذا
    path('sales-returns/<int:id>/update/', views.sales_return_update, name='sales_return_update'),

]