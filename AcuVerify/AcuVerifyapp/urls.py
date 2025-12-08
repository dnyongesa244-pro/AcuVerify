from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_user, name='login'),
    path('register_staff/', views.register_staff, name='register_staff'),
    path('register_student/', views.register_student, name='register_student'),
]