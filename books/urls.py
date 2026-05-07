from django.urls import include
from rest_framework.routers import DefaultRouter, path

from books.views import BookViewSet

app_name = "books"

router = DefaultRouter()
router.register("", BookViewSet, basename="book")

urlpatterns = [
    path("", include(router.urls)),
]
