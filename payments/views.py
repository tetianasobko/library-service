import os

from rest_framework import mixins, viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from stripe import StripeClient

from payments.models import Payment
from payments.serializers import PaymentSerializer


class PaymentViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Payment.objects.select_related("borrowing__user", "borrowing__book").all()
    serializer_class = PaymentSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(borrowing__user=self.request.user)
        return queryset

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payment = serializer.save()

        client = StripeClient(os.getenv("STRIPE_SECRET_KEY"))
        session = client.v1.checkout.sessions.create({
            "line_items": [{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": int(payment.money_to_pay * 100),
                    "product_data": {
                        "name": f"{payment.borrowing.book.title} ({payment.get_type_display()})",
                    },
                },
                "quantity": 1,
            }],
            "mode": "payment",
            "success_url": f"http://localhost:8000/api/payments/{payment.id}/",
            "cancel_url": "http://localhost:8000/api/payments/",
        })

        payment.session_id = session.id
        payment.session_url = session.url
        payment.save(update_fields=["session_id", "session_url"])

        return Response(self.get_serializer(payment).data, status=status.HTTP_201_CREATED)
