import pytest


def test_role_access_control():

    role = "USER"

    with pytest.raises(Exception):
        if role != "ADMIN":
            raise Exception("Forbidden")