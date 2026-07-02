from django.urls import path
from . import views
from django.contrib.auth import views as auth_views




urlpatterns = [
    
    path('', views.dashboard, name='dashboard'),
    #  DJANGO AUTH (Admin/University)
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # path('accounts/logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    # path('accounts/logout/', auth_views.LogoutView.as_view(next_page='/accounts/login/'), name='logout'),
    path('logout/', views.custom_logout, name='logout'),
    
    
    # ========== TEACHER AUTH (Independent) ==========
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/logout/', views.teacher_logout, name='teacher_logout'),
 
   #========== Attendance Management ==========
    path('attendance/', views.attendance_dashboard, name='attendance_dashboard'),
    path('attendance/sessions/', views.session_list, name='session_list'),
    path('attendance/session/create/', views.session_create, name='session_create'),
    path('attendance/session/<int:session_id>/', views.session_detail, name='session_detail'),
    
    # Attendance Taking
    path('attendance/session/<int:session_id>/take/', views.take_attendance, name='take_attendance'),
    path('attendance/session/<int:session_id>/edit/', views.edit_attendance, name='edit_attendance'),
    
    
    # QR Code System
    path('attendance/session/<int:session_id>/qr/generate/', views.generate_qr, name='generate_qr'),
    path('attendance/session/<int:session_id>/qr/display/', views.qr_display, name='qr_display'),
    path('attendance/qr/<uuid:qr_uuid>/', views.qr_checkin, name='qr_checkin'),
    path('attendance/qr/success/<int:attendance_id>/', views.qr_success, name='qr_success'),
    
    # Reports
    path('attendance/report/', views.attendance_report, name='attendance_report'),
    path('attendance/student/<int:student_id>/', views.student_attendance_detail, name='student_attendance_detail'),
    path('attendance/low-attendance/', views.low_attendance_report, name='low_attendance_report'),

    #student CRUD views
    
    path('students/',views.student_list,name='student_list'),
    path('students/add/',views.add_student,name='add_student'),
    path('students/<int:id>/',views.student_detail,name='student_detail'),
    path('students/edit/<int:id>/',views.edit_student,name='edit_student'),
    path('students/delete/<int:id>/',views.delete_student,name='delete_student'),
    
    #department CRUD views
    path('departments/',views.department_list,name='department_list'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/<int:id>/',views.department_detail,name='department_detail'),
    path('departments/edit/<int:id>/',views.edit_department,name='edit_department'),
    path('departments/delete/<int:id>/',views.delete_department,name='delete_department'),
    
    #subject CRUD views
    path('subjects/', views.subject_list, name='subject_list'),
    path('subjects/add/', views.subject_create, name='subject_create'),
    path('subjects/select/', views.subject_select, name='subject_select'),
    path('subjects/department/<int:department_id>/', views.subject_department_list, name='subject_department_list'),
    path('subjects/<int:id>/', views.subject_detail, name='subject_detail'),
    path('subjects/edit/<int:pk>/', views.subject_update, name='subject_update'),
    path('subjects/delete/<int:pk>/', views.subject_delete, name='subject_delete'),

    #teacher CRUD views
    path('teachers/',views.teacher_list,name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/<int:id>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/edit/<int:id>/', views.edit_teacher, name='edit_teacher'),
    path('teachers/delete/<int:id>/', views.delete_teacher, name='delete_teacher'),
    

  
    path('results/',views.result_list,name='result_list'),
    path('fees/',views.fee_list,name='fee_list'),
    path('users/', views.user_list, name='user_list'),
    path('profile/', views.profile, name='profile'),
    
]
