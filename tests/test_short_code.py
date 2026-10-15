

import string

import pytest

from app.main import generate_short_code


ALLOWED_CHARACTERS = string.ascii_letters + string.digits


def test_generate_short_code():
    code = generate_short_code()

    # The database schema requires six-character codes.
    assert len(code) == 6

    # Restrict codes to the Base62 alphabet used by the generator.
    assert all(char in ALLOWED_CHARACTERS for char in code)


@pytest.mark.parametrize("length", [1, 6, 10])
def test_generate_short_code_with_length(length):
    code = generate_short_code(length)

    # The function supports configurable lengths; six is only the default.
    assert len(code) == length

    # Random generation does not guarantee uniqueness; collision handling is tested separately.
    assert all(char in ALLOWED_CHARACTERS for char in code)