from decimal import Decimal, ROUND_HALF_UP


def quantize_two_places(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)