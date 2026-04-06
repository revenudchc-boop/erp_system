from django.urls import path
from . import views

urlpatterns = [
    path('', views.customers_list, name='customers_list'),
    path('create/', views.customers_create, name='customers_create'),
    path('<int:id>/', views.customers_detail, name='customers_detail'),
    path('<int:id>/update/', views.customers_update, name='customers_update'),
    path('<int:id>/delete/', views.customers_delete, name='customers_delete'),
    path('<int:id>/statement/', views.customers_statement, name='customers_statement'),
]