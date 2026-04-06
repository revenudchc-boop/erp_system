from django.urls import path
from . import views

urlpatterns = [
    path('company/', views.company_settings, name='company_settings'),
]