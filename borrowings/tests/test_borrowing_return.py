import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing


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


def sample_borrowing(user, book, **params):
    defaults = {
        "borrow_date": datetime.date.today() - datetime.timedelta(days=3),
        "expected_return_date": datetime.date.today() + datetime.timedelta(days=4),
        "actual_return_date": None,
        "book": book,
        "user": user,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


def return_url(borrowing_id):
    return reverse("borrowings:borrowing-return-borrowing", args=[borrowing_id])


class BorrowingReturnTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)

    def test_return_sets_actual_return_date(self):
        book = sample_book()
        borrowing = sample_borrowing(self.user, book)

        res = self.client.post(return_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.actual_return_date, datetime.date.today())

    def test_return_increases_book_inventory(self):
        book = sample_book(inventory=2)
        borrowing = sample_borrowing(self.user, book)

        self.client.post(return_url(borrowing.id))

        book.refresh_from_db()
        self.assertEqual(book.inventory, 3)

    def test_double_return_fails(self):
        book = sample_book()
        borrowing = sample_borrowing(
            self.user, book, actual_return_date=datetime.date.today()
        )

        res = self.client.post(return_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_double_return_does_not_increase_inventory(self):
        book = sample_book(inventory=4)
        borrowing = sample_borrowing(
            self.user, book, actual_return_date=datetime.date.today()
        )

        self.client.post(return_url(borrowing.id))

        book.refresh_from_db()
        self.assertEqual(book.inventory, 4)

    def test_unauthenticated_cannot_return(self):
        book = sample_book()
        borrowing = sample_borrowing(self.user, book)
        self.client.force_authenticate(user=None)

        res = self.client.post(return_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_return_other_users_borrowing(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com", password="testpass123"
        )
        book = sample_book()
        borrowing = sample_borrowing(other_user, book)

        res = self.client.post(return_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_return_any_borrowing(self):
        admin = get_user_model().objects.create_user(
            email="admin@example.com", password="testpass123", is_staff=True
        )
        book = sample_book(inventory=1)
        borrowing = sample_borrowing(self.user, book)
        self.client.force_authenticate(user=admin)

        res = self.client.post(return_url(borrowing.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        borrowing.refresh_from_db()
        self.assertEqual(borrowing.actual_return_date, datetime.date.today())
        book.refresh_from_db()
        self.assertEqual(book.inventory, 2)
