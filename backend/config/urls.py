from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

# GET /health/ is answered by common.middleware.HealthCheckMiddleware.

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),

    path("api/auth/", include("apps.accounts.urls")),
    path("api/users/", include("apps.accounts.urls_users")),
    path("api/production/", include("apps.production.urls")),
    path("api/inventory/", include("apps.inventory.urls")),
    path("api/suppliers/", include("apps.suppliers.urls")),
    path("api/analytics/", include("apps.analytics.urls")),
]

if settings.ENABLE_API_DOCS:
    urlpatterns += [
        path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
        path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    ]

admin.site.site_header = "Matna Visibility — Administration"
admin.site.site_title = "Matna Admin"
