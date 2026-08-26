_CONFUSABLES = str.maketrans({"o": "0", "i": "1", "l": "1", "b": "8"})


def match_key(value: str) -> str:
    """Return a transient key for extraction identity comparisons."""
    if not isinstance(value, str):
        raise TypeError("match_key requires a string")
    return "".join(character for character in value.casefold() if not character.isspace()).translate(_CONFUSABLES)


def values_match(left: str, right: str) -> bool:
    """Compare two extraction identity strings through :func:`match_key`."""
    if not isinstance(left, str) or not isinstance(right, str):
        raise TypeError("values_match requires two strings")
    return match_key(left) == match_key(right)
