from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health() -> dict[str, str]:
	"""Health check для Docker и load balancer."""
	return {"status": "ok"}
