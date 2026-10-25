from django.conf import settings
from rest_framework import serializers


def reason_field():
    limits = settings.PLATFORM_SETTINGS
    return serializers.CharField(
        min_length=limits["REASON_MIN_LENGTH"], max_length=limits["REASON_MAX_LENGTH"], trim_whitespace=True
    )


class VoidSerializer(serializers.Serializer):
    """Payload for voiding a production entry or delivery."""

    reason = reason_field()
