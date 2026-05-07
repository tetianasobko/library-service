from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token_obtain_pair")


class CreateUserViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_create_user_successful(self):
        payload = {"email": "new@example.com", "password": "testpass123"}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_create_user_with_short_password_fails(self):
        res = self.client.post(
            CREATE_USER_URL, {"email": "a@b.com", "password": "pw"}
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtain_token_with_valid_credentials(self):
        get_user_model().objects.create_user(
            email="login@example.com", password="testpass123"
        )
        res = self.client.post(
            TOKEN_URL,
            {"email": "login@example.com", "password": "testpass123"},
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)

    def test_obtain_token_with_wrong_password_fails(self):
        get_user_model().objects.create_user(
            email="login@example.com", password="testpass123"
        )
        res = self.client.post(
            TOKEN_URL,
            {"email": "login@example.com", "password": "wrongpass"},
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
