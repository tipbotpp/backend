import pytest


class ForbiddenError(Exception):
	pass


def test_role_access_control() -> None:
	role = "USER"

	with pytest.raises(ForbiddenError):
		if role != "ADMIN":
			raise ForbiddenError("Forbidden")
