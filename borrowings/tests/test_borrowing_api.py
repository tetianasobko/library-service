import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing

BORROWINGS_URL = reverse("borrowings:borrowing-list")


def detail_url(borrowing_id):
    return reverse("borrowings:borrowing-detail", args=[borrowing_id])


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


def sample_borrowing(user, book=None, **params):
    if book is None:
        book = sample_book()
    defaults = {
        "borrow_date": datetime.date.today(),
        "expected_return_date": datetime.date.today() + datetime.timedelta(days=7),
        "book": book,
        "user": user,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


class BorrowingListDetailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_list_own_borrowings(self):
        sample_borrowing(user=self.user)
        sample_borrowing(user=self.user)

        res = self.client.get(BORROWINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_list_returns_only_own_borrowings(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com", password="testpass123"
        )
        sample_borrowing(user=self.user)
        sample_borrowing(user=other_user)

        res = self.client.get(BORROWINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_retrieve_borrowing_detail(self):
        borrowing = sample_borrowing(user=self.user)

        res = self.client.get(detail_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], borrowing.id)

    def test_borrowing_response_contains_full_book_details(self):
        book = sample_book(title="Nested Book")
        sample_borrowing(user=self.user, book=book)

        res = self.client.get(BORROWINGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data[0]["book"]["title"], "Nested Book")
        self.assertIn("author", res.data[0]["book"])

    def test_unauthenticated_cannot_list_borrowings(self):
        self.client.force_authenticate(user=None)
        res = self.client.get(BORROWINGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
