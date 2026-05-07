from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

MANAGE_USER_URL = reverse("user:manage")


class UserViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )

    def test_retrieve_authenticated_user_profile(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(MANAGE_USER_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], self.user.email)

    def test_manage_user_unauthenticated(self):
        res = self.client.get(MANAGE_USER_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_user_profile(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(MANAGE_USER_URL, {"password": "newpass123"})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpass123"))
