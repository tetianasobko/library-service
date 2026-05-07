from django.conf import settings
from django.db import models

from books.models import Book


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="borrowings")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrowings"
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(expected_return_date__gt=models.F("borrow_date")),
                name="expected_return_after_borrow",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(actual_return_date__isnull=True)
                    | models.Q(actual_return_date__gt=models.F("borrow_date"))
                ),
                name="actual_return_after_borrow",
            ),
        ]

    def __str__(self):
        return f"{self.user} borrowed {self.book} on {self.borrow_date}"
