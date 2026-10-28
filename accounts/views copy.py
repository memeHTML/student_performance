from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm, SetPasswordForm
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .decorators import AdminRequiredMixin, admin_required
from .forms import BootstrapMixin, LoginForm, UserCreateForm, UserUpdateForm
from .models import User


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    """Django 5 requires POST for logout (the navbar uses a small form)."""
    next_page = reverse_lazy('accounts:login')


@login_required
def profile(request):
    return render(request, 'accounts/profile.html')


@login_required
def password_change(request):
    form = PasswordChangeForm(request.user, request.POST or None)
    for f in form.fields.values():
        f.widget.attrs['class'] = 'form-control'
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)  # keep the user logged in
        messages.success(request, 'Your password was changed.')
        return redirect('accounts:profile')
    return render(request, 'accounts/form.html', {'form': form, 'title': 'Change Password'})


# ---------- Admin-only user management ----------

class UserListView(AdminRequiredMixin, ListView):
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.order_by('username')
        q = self.request.GET.get('q', '').strip()
        role = self.request.GET.get('role', '')
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(first_name__icontains=q)
                           | Q(last_name__icontains=q) | Q(email__icontains=q))
        if role in User.Role.values:
            qs = qs.filter(role=role)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['roles'] = User.Role.choices
        ctx['q'] = self.request.GET.get('q', '')
        ctx['selected_role'] = self.request.GET.get('role', '')
        return ctx


class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/form.html'
    success_url = reverse_lazy('accounts:user_list')
    extra_context = {'title': 'Create User'}

    def form_valid(self, form):
        messages.success(self.request, 'User created.')
        return super().form_valid(form)


class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/form.html'
    success_url = reverse_lazy('accounts:user_list')
    extra_context = {'title': 'Edit User'}

    def form_valid(self, form):
        # Stop an admin from locking themselves out
        if self.object == self.request.user and (
                not form.cleaned_data['is_active'] or form.cleaned_data['role'] != User.Role.ADMIN):
            messages.error(self.request, 'You cannot deactivate or demote your own account.')
            return self.form_invalid(form)
        messages.success(self.request, 'User updated.')
        return super().form_valid(form)


class UserDeleteView(AdminRequiredMixin, DeleteView):
    model = User
    template_name = 'accounts/user_confirm_delete.html'
    success_url = reverse_lazy('accounts:user_list')

    def form_valid(self, form):
        if self.object == self.request.user:
            messages.error(self.request, 'You cannot delete your own account.')
            return redirect('accounts:user_list')
        messages.success(self.request, 'User deleted.')
        return super().form_valid(form)


@admin_required
def user_set_password(request, pk):
    """Admin resets another user's password."""
    target = get_object_or_404(User, pk=pk)
    form = SetPasswordForm(target, request.POST or None)
    for f in form.fields.values():
        f.widget.attrs['class'] = 'form-control'
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'Password reset for {target.username}.')
        return redirect('accounts:user_list')
    return render(request, 'accounts/form.html',
                  {'form': form, 'title': f'Set Password for {target.username}'})
