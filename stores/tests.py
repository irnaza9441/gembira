from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Store, Drink, Review


class StoresBasicTests(TestCase):
	def setUp(self):
		# create store and a drink
		self.store = Store.objects.create(id=1, title='Cafe')
		self.drink = Drink.objects.create(name='Latte', store_id=self.store)
		self.client = Client()

	def test_add_customized_item_to_session_cart(self):
		resp = self.client.post(f'/stores/add/{self.drink.id}/', {'quantity': '2', 'milk': 'soy', 'sugar': 'less', 'addons': ['vanilla']}, follow=True)
		self.assertEqual(resp.status_code, 200)
		session = self.client.session
		cart = session.get('cart_drinks', [])
		self.assertTrue(isinstance(cart, list))
		self.assertEqual(len(cart), 1)
		item = cart[0]
		self.assertEqual(item['drink_id'], self.drink.id)
		self.assertEqual(item['quantity'], 2)
		self.assertEqual(item['customization'].get('milk'), 'soy')

	def test_submit_review_requires_login_and_creates(self):
		# create user and login
		user = User.objects.create_user(username='bob', password='pass')
		self.client.login(username='bob', password='pass')
		resp = self.client.post(f'/stores/review/{self.store.id}/', {'rating': '4', 'comment': 'Great!'}, follow=True)
		self.assertEqual(resp.status_code, 200)
		reviews = Review.objects.filter(store=self.store)
		self.assertEqual(reviews.count(), 1)
		r = reviews.first()
		self.assertEqual(r.rating, 4)
		self.assertEqual(r.user.username, 'bob')
