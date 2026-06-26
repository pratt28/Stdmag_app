from .models import Teacher
from django.contrib import messages
from django.shortcuts import redirect
class TeacherAuthMiddleware:
    """Simple middleware — just attaches teacher to request, NO redirects"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        teacher_id = request.session.get('teacher_id')
        if teacher_id:
            try:
                request.teacher = Teacher.objects.get(id=teacher_id)
                request.is_teacher = True
            except Teacher.DoesNotExist:
                request.teacher = None
                request.is_teacher = False
                if 'teacher_id' in request.session:
                    del request.session['teacher_id']
        else:
            request.teacher = None
            request.is_teacher = False
        
        # Let the decorator handle access control — NO redirects here
        response = self.get_response(request)
        return response
# class TeacherAuthMiddleware:
#     """Custom middleware to handle teacher authentication via session"""
    
#     def __init__(self, get_response):
#         self.get_response = get_response
    
#     def __call__(self, request):
#         # Check if teacher is logged in via session
#         teacher_id = request.session.get('teacher_id')
#         if teacher_id:
#             try:
#                 request.teacher = Teacher.objects.get(id=teacher_id)
#                 request.is_teacher = True
#             except Teacher.DoesNotExist:
#                 request.teacher = None
#                 request.is_teacher = False
#                 del request.session['teacher_id']
#         else:
#             request.teacher = None
#             request.is_teacher = False
        
#         response = self.get_response(request)
#         return response


# class TeacherAuthMiddleware:
#     """Custom middleware to handle teacher authentication via session"""
    
#     def __init__(self, get_response):
#         self.get_response = get_response
    
#     def __call__(self, request):
#         # Check if teacher is logged in via session
#         teacher_id = request.session.get('teacher_id')
#         if teacher_id:
#             from .models import Teacher
#             try:
#                 request.teacher = Teacher.objects.get(id=teacher_id)
#                 request.is_teacher = True
#             except Teacher.DoesNotExist:
#                 request.teacher = None
#                 request.is_teacher = False
#                 del request.session['teacher_id']
#         else:
#             request.teacher = None
#             request.is_teacher = False
        
#         # 🔴 SECURITY: If admin is logged in, they CANNOT access teacher pages
#         # Teacher URLs that should be protected
#         teacher_urls = [
#             '/attendance/', '/attendance/sessions/', '/attendance/session/',
#             '/attendance/report/', '/attendance/student/', '/attendance/low-attendance/',
#             '/teacher/logout/'
#         ]
        
#         current_path = request.path_info
        
#         is_teacher_page = any(current_path.startswith(url) for url in teacher_urls)
        
#         if is_teacher_page:
#             # If no teacher session but admin is logged in → redirect to teacher login
#             if not request.is_teacher and request.user.is_authenticated:
#                 messages.error(request, "Admin users must login as teacher to access this area.")
#                 return redirect('teacher_login')
            
#             # If no teacher session and no admin → normal redirect to login
#             if not request.is_teacher and not request.user.is_authenticated:
#                 messages.error(request, "Please login as teacher to access this page.")
#                 return redirect('teacher_login')
        
#         response = self.get_response(request)
#         return response