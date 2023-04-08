from django.urls import path, include
from rest_framework import routers
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.api.urls import urlpatterns

# Settings
from config.settings import DEBUG

api = routers.DefaultRouter()
api.trailing_slash = "/?"

# Users API
# api.register(r"users", UserViewSet)

urls = (
    api.urls
    + urlpatterns
    + [
        path("auth/", include("rest_framework.urls", namespace="rest_framework")),
    ]
)


if DEBUG:
    urls += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "schema/swagger/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger",
        ),
        path(
            "schema/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]
