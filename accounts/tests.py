from django.test import TestCase
from django.urls import reverse

from .models import User


class RoleAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user('admin1', password='Pass12345!', role=User.Role.ADMIN)
        self.faculty = User.objects.create_user('fac1', password='Pass12345!', role=User.Role.FACULTY)
        self.student = User.objects.create_user('stu1', password='Pass12345!', role=User.Role.STUDENT)

    def test_anonymous_redirected_to_login(self):
        r = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(r.status_code, 302)
        self.assertIn('/accounts/login/', r.url)

    def test_admin_can_manage_users(self):
        self.client.login(username='admin1', password='Pass12345!')
        self.assertEqual(self.client.get(reverse('accounts:user_list')).status_code, 200)

    def test_faculty_and_student_forbidden(self):
        for name in ('fac1', 'stu1'):
            self.client.login(username=name, password='Pass12345!')
            self.assertEqual(self.client.get(reverse('accounts:user_list')).status_code, 403)
            self.client.logout()

    def test_superuser_gets_admin_role(self):
        su = User.objects.create_superuser('root', 'r@x.com', 'Pass12345!')
        self.assertEqual(su.role, User.Role.ADMIN)
