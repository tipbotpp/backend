import pytest
from src.services.auth import AuthService


@pytest.mark.asyncio
async def test_auth_service_check_access():

    service = AuthService()

    user = {"role": "USER"}

    result = service.check_access(user, "USER")

    assert result is True