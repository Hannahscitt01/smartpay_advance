from django.http import HttpResponseForbidden
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            # Dynamic role check using profile
            if hasattr(user, "profile") and user.profile.role == "ADMIN":
                return view_func(request, *args, **kwargs)
            
            # Optional: check Django groups
            if user.groups.filter(name="Admin").exists():
                return view_func(request, *args, **kwargs)
        
        return HttpResponseForbidden("You are not authorized to access this page.")
    return wrapper
