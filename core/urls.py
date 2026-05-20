from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('trail-work/', views.trail_work, name='trail_work'),
    path('announcements/<int:pk>/', views.announcement_detail, name='announcement_detail'),
    path('trail-conditions/', views.trail_conditions, name='trail_conditions'),
    path('trail-conditions/<int:pk>/', views.trail_condition_detail, name='trail_condition_detail'),
    path('map/', views.map_view, name='map'),
    path('map/data/', views.map_data, name='map_data'),
    path('trails/<int:pk>.gpx', views.trail_segment_gpx, name='trail_segment_gpx'),
]
