import datetime
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from books.models import Book
from borrowings.models import Borrowing
from payments.models import Payment

PAYMENTS_URL = reverse("payments:payment-list")


def payment_url(payment_id):
    return reverse("payments:payment-detail", args=[payment_id])


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


def sample_borrowing(user, **params):
    book = params.pop("book", None) or sample_book()
    defaults = {
        "borrow_date": datetime.date.today(),
        "expected_return_date": datetime.date.today() + datetime.timedelta(days=7),
        "book": book,
        "user": user,
    }
    defaults.update(params)
    return Borrowing.objects.create(**defaults)


def sample_payment(user, **params):
    borrowing = params.pop("borrowing", None) or sample_borrowing(user)
    defaults = {"borrowing": borrowing, "type": Payment.Type.PAYMENT}
    defaults.update(params)
    return Payment.objects.create(**defaults)


def mock_stripe_session():
    session = MagicMock()
    session.id = "cs_test_123"
    session.url = "https://checkout.stripe.com/pay/cs_test_123"
    return session


class PaymentListTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.admin = get_user_model().objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )

    def test_unauthenticated_cannot_list_payments(self):
        res = self.client.get(PAYMENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_sees_only_own_payments(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com", password="testpass123"
        )
        sample_payment(self.user)
        sample_payment(other_user)

        self.client.force_authenticate(user=self.user)
        res = self.client.get(PAYMENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)

    def test_admin_sees_all_payments(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com", password="testpass123"
        )
        sample_payment(self.user)
        sample_payment(other_user)

        self.client.force_authenticate(user=self.admin)
        res = self.client.get(PAYMENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)


class PaymentDetailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.payment = sample_payment(self.user)

    def test_retrieve_own_payment(self):
        res = self.client.get(payment_url(self.payment.id))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["id"], self.payment.id)

    def test_cannot_retrieve_other_users_payment(self):
        other_user = get_user_model().objects.create_user(
            email="other@example.com", password="testpass123"
        )
        other_payment = sample_payment(other_user)

        res = self.client.get(payment_url(other_payment.id))
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)


class PaymentCreateTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=self.user)
        self.borrowing = sample_borrowing(self.user)

    def test_unauthenticated_cannot_create_payment(self):
        self.client.force_authenticate(user=None)
        payload = {"borrowing": self.borrowing.id, "type": Payment.Type.PAYMENT}

        res = self.client.post(PAYMENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("payments.views.StripeClient")
    def test_create_payment_creates_stripe_session(self, mock_stripe_cls):
        mock_stripe_cls.return_value.v1.checkout.sessions.create.return_value = mock_stripe_session()
        payload = {"borrowing": self.borrowing.id, "type": Payment.Type.PAYMENT}

        res = self.client.post(PAYMENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Payment.objects.count(), 1)
        payment = Payment.objects.first()
        self.assertEqual(payment.session_id, "cs_test_123")
        self.assertEqual(payment.session_url, "https://checkout.stripe.com/pay/cs_test_123")

    @patch("payments.views.StripeClient")
    def test_create_payment_calculates_money_to_pay(self, mock_stripe_cls):
        mock_stripe_cls.return_value.v1.checkout.sessions.create.return_value = mock_stripe_session()
        payload = {"borrowing": self.borrowing.id, "type": Payment.Type.PAYMENT}

        self.client.post(PAYMENTS_URL, payload)

        payment = Payment.objects.first()
        # daily_fee=1.50, borrow period=7 days
        self.assertEqual(payment.money_to_pay, 1.50 * 7)

    @patch("payments.views.StripeClient")
    def test_create_payment_response_contains_session_url(self, mock_stripe_cls):
        mock_stripe_cls.return_value.v1.checkout.sessions.create.return_value = mock_stripe_session()
        payload = {"borrowing": self.borrowing.id, "type": Payment.Type.PAYMENT}

        res = self.client.post(PAYMENTS_URL, payload)

        self.assertIn("session_url", res.data)
        self.assertEqual(res.data["session_url"], "https://checkout.stripe.com/pay/cs_test_123")

    @patch("payments.views.StripeClient")
    def test_create_payment_status_defaults_to_pending(self, mock_stripe_cls):
        mock_stripe_cls.return_value.v1.checkout.sessions.create.return_value = mock_stripe_session()
        payload = {"borrowing": self.borrowing.id, "type": Payment.Type.PAYMENT}

        self.client.post(PAYMENTS_URL, payload)

        payment = Payment.objects.first()
        self.assertEqual(payment.status, Payment.Status.PENDING)
