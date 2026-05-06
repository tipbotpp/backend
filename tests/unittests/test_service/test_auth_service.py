import pytest
from src.services.auth import AuthService


@pytest.mark.asyncio
async def test_auth_service_check_access() -> None:
	service = AuthService()

	result = await service.check_access(role="USER", required_role="USER")

	assert result is True
