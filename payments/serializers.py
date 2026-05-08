from rest_framework import serializers

from borrowings.models import Borrowing
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            "id",
            "status",
            "type",
            "borrowing",
            "money_to_pay",
            "session_url",
            "session_id",
        )
        read_only_fields = ("status", "money_to_pay", "session_url", "session_id")
