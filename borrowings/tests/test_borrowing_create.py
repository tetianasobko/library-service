import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing

BORROWINGS_URL = reverse("borrowings:borrowing-list")


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


def borrowing_payload(book, **params):
    defaults = {
        "borrow_date": datetime.date.today(),
        "expected_return_date": datetime.date.today() + datetime.timedelta(days=7),
        "book": book.id,
    }
    defaults.update(params)
    return defaults


class BorrowingCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_create_borrowing_successful(self):
        book = sample_book()
        payload = borrowing_payload(book)

        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Borrowing.objects.count(), 1)
        borrowing = Borrowing.objects.first()
        self.assertEqual(borrowing.user, self.user)

    def test_create_borrowing_decreases_inventory(self):
        book = sample_book(inventory=3)
        payload = borrowing_payload(book)

        self.client.post(BORROWINGS_URL, payload)

        book.refresh_from_db()
        self.assertEqual(book.inventory, 2)

    def test_create_borrowing_with_zero_inventory_fails(self):
        book = sample_book(inventory=0)
        payload = borrowing_payload(book)

        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Borrowing.objects.count(), 0)

    def test_create_borrowing_links_to_current_user(self):
        book = sample_book()
        payload = borrowing_payload(book)

        res = self.client.post(BORROWINGS_URL, payload)

        borrowing = Borrowing.objects.get(id=res.data["id"])
        self.assertEqual(borrowing.user, self.user)

    def test_create_borrowing_invalid_dates_fails(self):
        book = sample_book()
        payload = borrowing_payload(
            book,
            expected_return_date=datetime.date.today() - datetime.timedelta(days=1),
        )

        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_cannot_create_borrowing(self):
        self.client.force_authenticate(user=None)
        book = sample_book()
        payload = borrowing_payload(book)

        res = self.client.post(BORROWINGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
