from rest_framework import serializers

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

    def validate_borrowing(self, borrowing):
        request = self.context["request"]
        if not request.user.is_staff and borrowing.user != request.user:
            raise serializers.ValidationError(
                "You can only create payments for your own borrowings."
            )
        return borrowing
