"""Privacy and data masking utilities for sensitive QRIS and CPM payload values."""


def mask_sensitive_value(value: str) -> str:
    """Mask sensitive identifiers such as PAN or Account Numbers.

    - If length <= 4: completely masked with asterisks.
    - If length <= 8: masks all characters except first character.
    - If length > 8: keeps the first 4 and last 4 characters, masks middle with asterisks.
    """
    if not value:
        return ""
    length = len(value)
    if length <= 4:
        return "*" * length
    if length <= 8:
        return value[0] + "*" * (length - 1)
    return value[:4] + "*" * (length - 8) + value[-4:]


def mask_cardholder_name(name: str) -> str:
    """Mask cardholder name while preserving initial letter."""
    if not name:
        return ""
    if len(name) <= 1:
        return "*"
    return name[0] + "*" * (len(name) - 1)
