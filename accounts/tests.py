from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse


class ManagerLoginTests(TestCase):
	def test_staff_user_redirected_to_admin(self):
		user = User.objects.create_user(username='manager', password='pass')
		user.is_staff = True
		user.save()

		resp = self.client.post(reverse('accounts.manager_login'), {
			'username': 'manager', 'password': 'pass'
		})

		# Should redirect to admin index
		self.assertEqual(resp.status_code, 302)
		self.assertTrue(resp['Location'].endswith('/admin/'))

	def test_non_staff_user_shown_error(self):
		user = User.objects.create_user(username='alice', password='pass')

		resp = self.client.post(reverse('accounts.manager_login'), {
			'username': 'alice', 'password': 'pass'
		})

		# Non-staff users should get an error rendered on the login page
		self.assertEqual(resp.status_code, 200)
		self.assertContains(resp, 'You are not authorized to access the admin dashboard.')
