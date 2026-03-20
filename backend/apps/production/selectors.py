from .models import ProductionEntry


def get_production_entries():
    return ProductionEntry.objects.select_related("created_by", "updated_by").all()