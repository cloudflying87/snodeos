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
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/data/', views.calendar_data, name='calendar_data'),
    path('events/<int:pk>/', views.event_detail, name='event_detail'),
    path('events/<int:pk>/signup/', views.event_signup, name='event_signup'),
    path('events/<int:pk>/withdraw/', views.event_withdraw, name='event_withdraw'),

    # Messaging
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/new/', views.inbox_compose, name='inbox_compose'),
    path('inbox/mark-all-read/', views.inbox_mark_all_read, name='inbox_mark_all_read'),
    path('inbox/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('inbox/<int:pk>/mark-read/', views.conversation_mark_read, name='conversation_mark_read'),

    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/open/', views.notification_open, name='notification_open'),
    path('notifications/mark-all-read/', views.notifications_mark_all_read, name='notifications_mark_all_read'),

    # iCal feeds
    path('calendar.ics',         views.calendar_ics,         name='calendar_ics'),
    path('members/calendar.ics', views.members_calendar_ics, name='members_calendar_ics'),

    # Member photo submissions
    path('share-photo/', views.share_photo, name='share_photo'),
]
