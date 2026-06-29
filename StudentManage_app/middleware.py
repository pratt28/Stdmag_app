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
