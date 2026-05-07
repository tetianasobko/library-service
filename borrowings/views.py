from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from borrowings.models import Borrowing
from borrowings.serializers import BorrowingReadSerializer


class BorrowingViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = BorrowingReadSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Borrowing.objects.filter(user=self.request.user).select_related("book", "user")
