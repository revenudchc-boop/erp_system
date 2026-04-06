from django.urls import path
from . import views

urlpatterns = [
    # العملات
    path('', views.currencies_list, name='currencies_list'),
    path('create/', views.currencies_create, name='currencies_create'),
    path('<int:id>/update/', views.currencies_update, name='currencies_update'),
    path('<int:id>/delete/', views.currencies_delete, name='currencies_delete'),
    
    # أسعار الصرف
    path('rates/', views.exchange_rates, name='exchange_rates'),
    path('rates/update/', views.update_exchange_rate, name='update_exchange_rate'),
    
    # API
    path('rate/<str:code>/', views.get_exchange_rate, name='get_exchange_rate'),
]