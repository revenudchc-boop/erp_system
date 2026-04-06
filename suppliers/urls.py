from django.urls import path
from . import views

urlpatterns = [
    path('', views.suppliers_list, name='suppliers_list'),
    path('create/', views.suppliers_create, name='suppliers_create'),
    path('<int:id>/', views.suppliers_detail, name='suppliers_detail'),
    path('<int:id>/update/', views.suppliers_update, name='suppliers_update'),
    path('<int:id>/delete/', views.suppliers_delete, name='suppliers_delete'),
    path('<int:id>/statement/', views.suppliers_statement, name='suppliers_statement'),
]