import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from app.views import PRODUCT_CATALOG
from app.models import ContactMessage
from recommendation import get_recommendations


class AuthenticationTests(TestCase):
    def test_registration_creates_hashed_user_and_session(self):
        response = self.client.post(
            reverse('register_api'),
            data=json.dumps({
                'name': 'Shovon Das',
                'email': 'shovon@example.com',
                'password': 'A-secure-password-123',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username='shovon@example.com')
        self.assertTrue(user.check_password('A-secure-password-123'))
        self.assertNotEqual(user.password, 'A-secure-password-123')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.id)

    def test_invalid_registration_is_rejected(self):
        response = self.client.post(
            reverse('register_api'),
            data=json.dumps({
                'name': 'Test User',
                'email': 'not-an-email',
                'password': 'short',
            }),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(User.objects.count(), 0)

    def test_checkout_requires_authentication(self):
        response = self.client.get(reverse('checkout'))

        self.assertRedirects(response, '/login?next=/checkout')

    def test_anonymous_cart_is_rejected(self):
        response = self.client.get(reverse('cart_api'))

        self.assertEqual(response.status_code, 401)

    def test_each_user_has_a_separate_cart(self):
        first_user = User.objects.create_user(
            username='first@example.com',
            password='A-secure-password-123',
        )
        second_user = User.objects.create_user(
            username='second@example.com',
            password='A-secure-password-123',
        )

        self.client.force_login(first_user)
        self.client.post(
            reverse('cart_api'),
            data=json.dumps({'action': 'add', 'slug': 'rainbow-day-hoodie', 'quantity': 1}),
            content_type='application/json',
        )
        self.client.force_login(second_user)
        response = self.client.get(reverse('cart_api'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['items'], [])

    def test_about_and_contact_pages_are_available(self):
        self.assertEqual(self.client.get(reverse('about')).status_code, 200)
        self.assertEqual(self.client.get(reverse('contact')).status_code, 200)

    def test_contact_form_saves_user_message(self):
        response = self.client.post(
            reverse('contact'),
            {
                'name': 'Jane Doe',
                'email': 'jane@example.com',
                'subject': 'Shipping question',
                'message': 'When will my order arrive?',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ContactMessage.objects.count(), 1)
        saved = ContactMessage.objects.get()
        self.assertEqual(saved.name, 'Jane Doe')
        self.assertEqual(saved.email, 'jane@example.com')
        self.assertEqual(saved.subject, 'Shipping question')
        self.assertEqual(saved.message, 'When will my order arrive?')


class RecommendationTests(TestCase):
    def test_recommendations_rank_similar_products_and_exclude_current(self):
        recommendations = get_recommendations('kurotsuki', PRODUCT_CATALOG)
        recommended_slugs = [item['slug'] for item in recommendations]

        self.assertEqual(len(recommendations), 4)
        self.assertNotIn('kurotsuki', recommended_slugs)
        self.assertEqual(
            PRODUCT_CATALOG[recommended_slugs[0]]['category'],
            PRODUCT_CATALOG['kurotsuki']['category'],
        )

    def test_product_detail_renders_recommended_products(self):
        response = self.client.get(reverse('product_detail', args=['kurotsuki']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recommended for You')
        self.assertEqual(len(response.context['recommendations']), 4)

    def test_jeans_products_only_recommend_other_jeans(self):
        for slug in ('urban-denim-jeans', 'light-wash-wide-leg-jeans'):
            with self.subTest(slug=slug):
                recommendations = get_recommendations(slug, PRODUCT_CATALOG)

                self.assertTrue(recommendations)
                self.assertTrue(all(
                    'JEANS' in product['category'].upper()
                    for product in recommendations
                ))
