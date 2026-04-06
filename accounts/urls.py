from django.urls import path
from . import views

urlpatterns = [
    path('', views.account_list, name='account_list'),
    path('tree/', views.account_tree, name='account_tree'),
    path('api/list/', views.account_api_list, name='account_api_list'),
    path('create/', views.account_create, name='account_create'),
    path('<int:id>/', views.account_detail, name='account_detail'),
    path('<int:id>/update/', views.account_update, name='account_update'),
    path('<int:id>/delete/', views.account_delete, name='account_delete'),
]