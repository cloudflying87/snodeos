from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('trail-work/', views.trail_work, name='trail_work'),
    path('announcements/<int:pk>/', views.announcement_detail, name='announcement_detail'),
]
