import httpx

from src.core.exc.exceptions import (
	DonationRejectedStopwordError,
	DonationRejectedToxicityError,
)
from src.gateways import ml as ml_gateway
from src.schemas.dataclasses.ml import (
	ModerationRequestDTO,
	TTSRequestDTO,
	TTSResultDTO,
)


class MLService:
	def __init__(self, client: httpx.AsyncClient) -> None:
		self._client = client

	async def moderate(self, text: str, stopwords: list[str], streamer_id: int) -> None:
		"""Проверяет текст на токсичность и стоп-слова. Выбрасывает исключение если заблокировано."""
		result = await ml_gateway.check_moderation(
			self._client,
			ModerationRequestDTO(text=text, stopwords=stopwords, streamer_id=streamer_id),
		)
		if result.verdict == "rejected_stopword":
			raise DonationRejectedStopwordError()
		if result.verdict == "rejected_toxicity":
			raise DonationRejectedToxicityError()

	async def synthesize_tts(
		self,
		text: str,
		donor_name: str,
		amount: int,
		voice: str,
		donation_id: int,
	) -> TTSResultDTO:
		return await ml_gateway.synthesize_tts(
			self._client,
			TTSRequestDTO(
				text=text,
				donor_name=donor_name,
				amount=amount,
				voice=voice,
				donation_id=donation_id,
			),
		)
