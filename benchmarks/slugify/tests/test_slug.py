from src.slug import slugify


def test_slugify_lowercases_and_replaces_spaces():
    assert slugify("Hello World") == "hello-world"


def test_slugify_removes_punctuation():
    assert slugify("  Hello, World!  ") == "hello-world"


def test_slugify_collapses_repeated_spaces():
    assert slugify("small   steps") == "small-steps"
