import pytest
from src.services.auth import create_token, decode_token


def test_jwt_encode_decode():

    token = create_token({"user_id": 1, "role": "USER"})

    payload = decode_token(token)

    assert payload["user_id"] == 1
    assert payload["role"] == "USER"


def test_invalid_token():

    import pytest
    from src.services.auth import decode_token

    with pytest.raises(Exception):
        decode_token("invalid.token")