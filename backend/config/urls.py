from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),

    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

    path("api/auth/", include("apps.accounts.urls")),
    path("api/users/", include("apps.accounts.urls_users")),
    path("api/production/", include("apps.production.urls")),
    path("api/inventory/", include("apps.inventory.urls")),
    path("api/suppliers/", include("apps.suppliers.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
]