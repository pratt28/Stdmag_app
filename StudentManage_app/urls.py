from django.urls import path
from . import views


urlpatterns = [
    #student CRUD views
    path('',views.dashboard,name='dashboard'),
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
    path('subjects/department/<int:department_id>/', views.subject_department_list, name='subject_department_list'),
    path('subjects/<int:id>/', views.subject_detail, name='subject_detail'),
    path('subjects/edit/<int:pk>/', views.subject_update, name='subject_update'),
    path('subjects/delete/<int:pk>/', views.subject_delete, name='subject_delete'),

    #teacher CRUD views
    path('teachers/',views.teacher_list,name='teacher_list'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/edit/<int:id>/', views.edit_teacher, name='edit_teacher'),
    path('teachers/delete/<int:id>/', views.delete_teacher, name='delete_teacher'),

    path('attendance/', views.attendance_list, name='attendance_list'),
    path('results/',views.result_list,name='result_list'),
    path('fees/',views.fee_list,name='fee_list'),
    path('users/', views.user_list, name='user_list'),
    path('profile/', views.profile, name='profile'),
    
]
