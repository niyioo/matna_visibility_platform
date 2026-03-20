from django.urls import path
from .views import ProductionEntryListCreateView, ProductionEntryDetailView

urlpatterns = [
    path("entries/", ProductionEntryListCreateView.as_view(), name="production-entry-list-create"),
    path("entries/<uuid:pk>/", ProductionEntryDetailView.as_view(), name="production-entry-detail"),
]