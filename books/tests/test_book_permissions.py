from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book

BOOKS_URL = reverse("books:book-list")


def detail_url(book_id):
    return reverse("books:book-detail", args=[book_id])


def sample_book(**params):
    defaults = {
        "title": "Test Book",
        "author": "Test Author",
        "cover": Book.CoverType.HARD,
        "inventory": 5,
        "daily_fee": "1.50",
    }
    defaults.update(params)
    return Book.objects.create(**defaults)


class BookPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.regular_user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.admin_user = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )

    def test_unauthenticated_can_list_books(self):
        res = self.client.get(BOOKS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_can_retrieve_book(self):
        book = sample_book()
        res = self.client.get(detail_url(book.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_create_book(self):
        payload = {
            "title": "Book",
            "author": "Author",
            "cover": Book.CoverType.SOFT,
            "inventory": 1,
            "daily_fee": "1.00",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_create_book(self):
        self.client.force_authenticate(user=self.regular_user)
        payload = {
            "title": "Book",
            "author": "Author",
            "cover": Book.CoverType.SOFT,
            "inventory": 1,
            "daily_fee": "1.00",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_update_book(self):
        book = sample_book()
        self.client.force_authenticate(user=self.regular_user)
        res = self.client.patch(detail_url(book.id), {"inventory": 99})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_regular_user_cannot_delete_book(self):
        book = sample_book()
        self.client.force_authenticate(user=self.regular_user)
        res = self.client.delete(detail_url(book.id))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_book(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {
            "title": "Admin Book",
            "author": "Admin Author",
            "cover": Book.CoverType.HARD,
            "inventory": 3,
            "daily_fee": "2.50",
        }
        res = self.client.post(BOOKS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_admin_can_delete_book(self):
        book = sample_book()
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.delete(detail_url(book.id))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
