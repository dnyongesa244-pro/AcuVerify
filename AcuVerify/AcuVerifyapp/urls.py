"""
=============================================================================
AcuVerify URL Configuration
=============================================================================
URL routing for all views in the AcuVerifyapp.

URL patterns:
- Authentication: login, logout
- Registration: staff and student registration
- Administration: academic dashboard
- Stream assignment: admin-only page for assigning teachers to streams
- Staff management: list, edit, delete staff members
=============================================================================
"""

from django.urls import path
from . import views

urlpatterns = [
    # Public/Home pages
    path('', views.home, name='home'),
    
    # Authentication
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    
    # Registration
    path('register_staff/', views.register_staff, name='register_staff'),
    path('register_student/', views.register_student, name='register_student'),
    
    # Academic administration
    path('accademic/', views.accademic_view, name='accademic'),
    
    # Stream/Subject assignment (admin-only in view)
    path('assign-stream/', views.assign_stream, name='assign_stream'),
    
    # Staff management (CRUD)
    path('staff/', views.staff_list, name='staff_list'),
    path('staff/<int:pk>/edit/', views.edit_staff, name='edit_staff'),
    path('staff/<int:pk>/delete/', views.delete_staff, name='delete_staff'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('assign_stream_teacher/', views.assign_stream, name='assign_stream'),


    #student management (CRUD)    path('students/', views.student_list, name='student_list'),
    path('students/', views.student_list, name='student_list'),
    path('students/<int:pk>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:pk>/delete/', views.delete_student, name='delete_student'),
]
