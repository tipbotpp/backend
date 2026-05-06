from __future__ import annotations

from typing import cast

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.core.configs import cfg

router = APIRouter(prefix="/.well-known")


@router.get("/jwks.json", include_in_schema=False)
async def jwks() -> JSONResponse:
	"""
	Публикует RSA публичный ключ в формате JWKS.
	Другие сервисы могут верифицировать JWT без приватного ключа.
	"""
	from jwt.algorithms import RSAAlgorithm  # noqa: PLC0415

	jwk = RSAAlgorithm.to_jwk(
		cast(RSAPublicKey, load_pem_public_key(cfg.auth.jwt_public_key.encode())),
		as_dict=True,
	)
	jwk["use"] = "sig"
	jwk["alg"] = cfg.auth.jwt_algorithm
	jwk["kid"] = "tipbot-1"

	return JSONResponse({"keys": [jwk]})
