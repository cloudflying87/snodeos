from django.urls import path
from . import views

app_name = 'members'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('list/', views.member_list, name='member_list'),
    path('pending/', views.pending_applications, name='pending'),
    path('<int:pk>/', views.member_detail, name='member_detail'),
    path('<int:pk>/edit/', views.member_edit, name='member_edit'),
    path('<int:pk>/approve/', views.approve_member, name='approve_member'),
    path('<int:pk>/deactivate/', views.deactivate_member, name='deactivate_member'),
]
