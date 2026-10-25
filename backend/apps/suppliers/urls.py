from django.urls import path

from .views import (
    SupplierDeliveryDetailView,
    SupplierDeliveryListCreateView,
    SupplierDeliveryVoidView,
    SupplierDetailView,
    SupplierListCreateView,
)

urlpatterns = [
    path("", SupplierListCreateView.as_view(), name="supplier-list-create"),
    path("<uuid:pk>/", SupplierDetailView.as_view(), name="supplier-detail"),
    path("deliveries/", SupplierDeliveryListCreateView.as_view(), name="supplier-delivery-list-create"),
    path("deliveries/<uuid:pk>/", SupplierDeliveryDetailView.as_view(), name="supplier-delivery-detail"),
    path("deliveries/<uuid:pk>/void/", SupplierDeliveryVoidView.as_view(), name="supplier-delivery-void"),
]
