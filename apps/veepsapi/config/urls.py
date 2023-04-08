from django.contrib import admin
from django.urls import path, include

import apps.users.urls as auth_urls

from config.api_urls import urls as api_urls
from apps.api.views import HomeViewSet


urlpatterns = [
    path("", HomeViewSet.as_view(), name="home"),
    path("admin/", admin.site.urls, name="admin"),
    path("api/", include(api_urls)),
    path("api/auth/", include(auth_urls)),
]
