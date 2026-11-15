def is_palindrome(text: str) -> bool:
    """Return whether text reads the same forward and backward."""
    normalized = text.replace(" ", "").casefold()
    return normalized == normalized[::-1]
