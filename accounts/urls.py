from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.member_login, name='login'),
    path('logout/', views.member_logout, name='logout'),
]
