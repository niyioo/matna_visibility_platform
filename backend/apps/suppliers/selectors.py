from .models import Supplier, SupplierDelivery


def get_suppliers():
    return Supplier.objects.all()


def get_supplier_deliveries():
    return SupplierDelivery.objects.select_related("supplier", "received_by").all()