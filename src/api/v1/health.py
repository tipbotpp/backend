from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
	"""Health check endpoint для Docker и load balancer."""
	return {"status": "ok"}
