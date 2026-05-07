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


class BookListDetailTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_list_books(self):
        sample_book(title="Book A")
        sample_book(title="Book B")

        res = self.client.get(BOOKS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)

    def test_retrieve_book_detail(self):
        book = sample_book()

        res = self.client.get(detail_url(book.id))

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], book.title)
        self.assertEqual(res.data["author"], book.author)


class BookWriteTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )
        self.client.force_authenticate(user=self.admin)

    def test_create_book(self):
        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": Book.CoverType.SOFT,
            "inventory": 3,
            "daily_fee": "2.00",
        }
        res = self.client.post(BOOKS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        book = Book.objects.get(id=res.data["id"])
        self.assertEqual(book.title, payload["title"])

    def test_update_book(self):
        book = sample_book()
        res = self.client.patch(detail_url(book.id), {"inventory": 10})

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        book.refresh_from_db()
        self.assertEqual(book.inventory, 10)

    def test_delete_book(self):
        book = sample_book()
        res = self.client.delete(detail_url(book.id))

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Book.objects.filter(id=book.id).exists())
