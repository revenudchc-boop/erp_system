from django.urls import path
from . import views

urlpatterns = [
    path('income-statement/', views.income_statement, name='income_statement'),
    path('balance-sheet/', views.balance_sheet, name='balance_sheet'),
    path('cash-flow/', views.cash_flow, name='cash_flow'),
    path('dashboard/', views.reports_dashboard, name='reports_dashboard'),
    path('adjustments/', views.adjustments_report, name='adjustments_report'),
]