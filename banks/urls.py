from django.urls import path
from . import views

urlpatterns = [
    # البنوك
    path('banks/', views.banks_list, name='banks_list'),
    path('banks/create/', views.bank_create, name='bank_create'),
    path('banks/<int:id>/', views.bank_detail, name='bank_detail'),
    path('banks/<int:id>/update/', views.bank_update, name='bank_update'),
    path('banks/<int:id>/delete/', views.bank_delete, name='bank_delete'),
    path('banks/<int:id>/statement/', views.bank_statement, name='bank_statement'),
    
    # الصناديق
    path('cash/', views.cash_list, name='cash_list'),
    path('cash/create/', views.cash_create, name='cash_create'),
    path('cash/<int:id>/update/', views.cash_update, name='cash_update'),
    path('cash/<int:id>/delete/', views.cash_delete, name='cash_delete'),
]