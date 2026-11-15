import unicodedata


def slugify(text: str) -> str:
    without_punctuation = "".join(
        character
        for character in text.lower()
        if not unicodedata.category(character).startswith("P")
    )
    return "-".join(without_punctuation.split()).strip("-")
