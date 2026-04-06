from django.urls import path
from . import views

urlpatterns = [
    # مراكز التكلفة
    path('centers/', views.cost_centers_list, name='cost_centers_list'),
    path('centers/tree/', views.cost_centers_tree, name='cost_centers_tree'),
    path('centers/create/', views.cost_center_create, name='cost_center_create'),
    path('centers/<int:id>/update/', views.cost_center_update, name='cost_center_update'),
    path('centers/<int:id>/delete/', views.cost_center_delete, name='cost_center_delete'),
    
    # عناصر التكلفة
    path('elements/', views.cost_elements_list, name='cost_elements_list'),
    path('elements/create/', views.cost_element_create, name='cost_element_create'),
    path('elements/<int:id>/update/', views.cost_element_update, name='cost_element_update'),
    path('elements/<int:id>/delete/', views.cost_element_delete, name='cost_element_delete'),
    
    # قواعد التوزيع
    path('rules/', views.allocation_rules_list, name='allocation_rules_list'),
    path('rules/create/', views.allocation_rule_create, name='allocation_rule_create'),
    path('rules/<int:id>/update/', views.allocation_rule_update, name='allocation_rule_update'),
    path('rules/<int:id>/delete/', views.allocation_rule_delete, name='allocation_rule_delete'),
    path('rules/<int:id>/run/', views.run_allocation_rule, name='run_allocation_rule'),
    
    # تقارير
    path('report/', views.cost_center_report, name='cost_center_report'),
]