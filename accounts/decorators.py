"""Role-based access helpers. Other members import these in their views.

Function views:
    from accounts.decorators import admin_required, faculty_or_admin_required

    @faculty_or_admin_required
    def mark_attendance(request): ...

Class-based views:
    from accounts.decorators import RoleRequiredMixin
    from accounts.models import User

    class StudentListView(RoleRequiredMixin, ListView):
        allowed_roles = (User.Role.ADMIN, User.Role.FACULTY)
"""
from functools import wraps

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .models import User


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return _wrapped
    return decorator


admin_required = role_required(User.Role.ADMIN)
faculty_required = role_required(User.Role.FACULTY)
student_required = role_required(User.Role.STUDENT)
faculty_or_admin_required = role_required(User.Role.ADMIN, User.Role.FACULTY)


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    allowed_roles = ()

    def test_func(self):
        return self.request.user.role in self.allowed_roles


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = (User.Role.ADMIN,)


class FacultyOrAdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = (User.Role.ADMIN, User.Role.FACULTY)
