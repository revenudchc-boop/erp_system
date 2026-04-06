from django.urls import path
from . import views

urlpatterns = [
    # المسارات العادية للواجهة
    path('entries/', views.entry_list, name='entry_list'),
    path('entries/create/', views.entry_create, name='entry_create'),
    path('entries/<int:id>/', views.entry_detail, name='entry_detail'),
    path('entries/<int:id>/update/', views.entry_update, name='entry_update'),
    path('entries/<int:id>/delete/', views.entry_delete, name='entry_delete'),
    path('entries/<int:id>/post/', views.entry_post, name='entry_post'),
    path('entries/<int:id>/unpost/', views.entry_unpost, name='entry_unpost'),
    path('trial-balance/', views.trial_balance, name='trial_balance'),
    
    # مسارات معاينة وطباعة القيد
    path('entry/<int:id>/', views.journal_entry_detail, name='journal_entry_detail'),
    path('entry/<int:id>/print/', views.journal_entry_print, name='journal_entry_print'),
    
    # مسارات API للواجهة الجديدة (JSON)
    path('api/entries/', views.api_entries_list, name='api_entries_list'),
    path('api/entries/create/', views.api_entry_create, name='api_entry_create'),
    path('api/entries/<int:id>/update/', views.api_entry_update, name='api_entry_update'),
    path('api/entries/<int:id>/post/', views.api_entry_post, name='api_entry_post'),
]