import pytest
from jwt import InvalidTokenError
from src.services.auth import create_token, decode_token


def test_jwt_encode_decode() -> None:
	token = create_token({"user_id": 1, "role": "USER"})
	payload = decode_token(token)

	assert payload["user_id"] == 1
	assert payload["role"] == "USER"


def test_invalid_token() -> None:
	with pytest.raises(InvalidTokenError):
		decode_token("invalid.token")
