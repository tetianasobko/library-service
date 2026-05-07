from django.db import transaction
from rest_framework import serializers

from books.serializers import BookSerializer
from borrowings.models import Borrowing


class BorrowingReadSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ("id", "borrow_date", "expected_return_date", "book")

    def validate(self, attrs):
        data = super(BorrowingCreateSerializer, self).validate(attrs) 
        inventory = attrs["book"].inventory
        expected_return_date = attrs["expected_return_date"]
        borrow_date = attrs["borrow_date"]
        Borrowing.validate_book_inventory(inventory, serializers.ValidationError)
        Borrowing.validate_return_date(
                expected_return_date, borrow_date, serializers.ValidationError
            )
        return data

    @transaction.atomic
    def create(self, validated_data):
        book = validated_data["book"]
        book.inventory -= 1
        book.save(update_fields=["inventory"])
        return super().create(validated_data)
