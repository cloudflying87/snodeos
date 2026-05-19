from django.urls import path
from . import views

app_name = 'manage_panel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    path('stats/', views.stats_edit, name='stats_edit'),

    path('officers/', views.officer_list, name='officer_list'),
    path('officers/add/', views.officer_add, name='officer_add'),
    path('officers/<int:pk>/edit/', views.officer_edit, name='officer_edit'),
    path('officers/<int:pk>/delete/', views.officer_delete, name='officer_delete'),
    path('officers/reorder/', views.officer_reorder, name='officer_reorder'),

    path('sponsors/', views.sponsor_list, name='sponsor_list'),
    path('sponsors/add/', views.sponsor_add, name='sponsor_add'),
    path('sponsors/<int:pk>/edit/', views.sponsor_edit, name='sponsor_edit'),
    path('sponsors/<int:pk>/delete/', views.sponsor_delete, name='sponsor_delete'),
    path('sponsors/<int:pk>/toggle/', views.sponsor_toggle, name='sponsor_toggle'),

    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/add/', views.announcement_add, name='announcement_add'),
    path('announcements/<int:pk>/edit/', views.announcement_edit, name='announcement_edit'),
    path('announcements/<int:pk>/delete/', views.announcement_delete, name='announcement_delete'),
    path('announcements/<int:pk>/pin/', views.announcement_pin, name='announcement_pin'),

    path('trail-work/', views.trail_work_list, name='trail_work_list'),
    path('trail-work/add/', views.trail_work_add, name='trail_work_add'),
    path('trail-work/<int:pk>/edit/', views.trail_work_edit, name='trail_work_edit'),
    path('trail-work/<int:pk>/delete/', views.trail_work_delete, name='trail_work_delete'),

    path('messages/', views.message_list, name='message_list'),
    path('messages/<int:pk>/', views.message_detail, name='message_detail'),
    path('messages/<int:pk>/delete/', views.message_delete, name='message_delete'),

    path('email/', views.email_settings, name='email_settings'),
]
