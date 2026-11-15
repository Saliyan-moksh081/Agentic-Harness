from src.palindrome import is_palindrome


def test_palindrome_ignores_case_and_spaces():
    assert is_palindrome("Never odd or even") is True


def test_non_palindrome_returns_false():
    assert is_palindrome("PatchPilot") is False


def test_empty_text_is_a_palindrome():
    assert is_palindrome("") is True
