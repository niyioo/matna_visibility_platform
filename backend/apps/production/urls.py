from django.urls import path

from .views import ProductionEntryDetailView, ProductionEntryListCreateView, ProductionEntryVoidView

urlpatterns = [
    path("entries/", ProductionEntryListCreateView.as_view(), name="production-entry-list-create"),
    path("entries/<uuid:pk>/", ProductionEntryDetailView.as_view(), name="production-entry-detail"),
    path("entries/<uuid:pk>/void/", ProductionEntryVoidView.as_view(), name="production-entry-void"),
]
