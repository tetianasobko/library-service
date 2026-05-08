from django.db import models


class Payment(models.Model):
    FINE_MULTIPLIER = 2

    class Status(models.TextChoices):
        PAID = "PAID", "Paid"
        PENDING = "PENDING", "Pending"

    class Type(models.TextChoices):
        PAYMENT = "PAYMENT", "Payment"
        FINE = "FINE", "Fine"

    status = models.CharField(max_length=7, choices=Status.choices, default=Status.PENDING)
    type = models.CharField(max_length=7, choices=Type.choices)
    borrowing = models.ForeignKey(
        "borrowings.Borrowing", on_delete=models.CASCADE, related_name="payments"
    )
    session_url = models.URLField(null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    money_to_pay = models.DecimalField(max_digits=6, decimal_places=2)

    def calculate_money_to_pay(self):
        if self.type == self.Type.PAYMENT:
            return self.borrowing.book.daily_fee * (
                (self.borrowing.expected_return_date - self.borrowing.borrow_date).days
            )
        elif self.type == self.Type.FINE:
            if self.borrowing.actual_return_date and self.borrowing.actual_return_date > self.borrowing.expected_return_date:
                return self.borrowing.book.daily_fee * self.FINE_MULTIPLIER * (
                    (self.borrowing.actual_return_date - self.borrowing.expected_return_date).days
                )
        return 0

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.money_to_pay = self.calculate_money_to_pay()
        super().save(*args, **kwargs)
