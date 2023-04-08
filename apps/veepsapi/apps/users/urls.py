from django.urls import path, include
from rest_framework import routers
from rest_framework.authtoken import views


from .views import (
    UserViewSet,
)

router = routers.SimpleRouter()

router.register(r"user", UserViewSet, basename="user")


urlpatterns = [
    path(r"", include(router.urls)),
    path(r"token/", views.obtain_auth_token, name="auth-token"),
]
