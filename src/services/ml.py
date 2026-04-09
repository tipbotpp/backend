import httpx

from src.core.exc.exceptions import DonationRejectedStopwordError, DonationRejectedToxicityError
from src.gateways import ml as ml_gateway
from src.schemas.dataclasses.ml import ModerationRequestDTO, TTSRequestDTO, TTSResultDTO
from src.services.logger import get_logger

logger = get_logger().bind(layer="service", module="ml")


class MLService:
	def __init__(self, client: httpx.AsyncClient) -> None:
		self._client = client

	async def moderate(self, text: str, stopwords: list[str], streamer_id: int) -> None:
		log = logger.bind(
			request_streamer_id=streamer_id,
			request_stopwords_count=len(stopwords),
			request_text_length=len(text),
		)
		log.debug("ml.moderate started")

		result = await ml_gateway.check_moderation(
			self._client,
			ModerationRequestDTO(text=text, stopwords=stopwords, streamer_id=streamer_id),
		)
		log.debug(
			"ml.moderate result",
			verdict=result.verdict,
			toxicity_score=result.toxicity_score,
			stopword_found=result.stopword_found,
		)

		if result.verdict == "rejected_stopword":
			log.info("ml.moderate rejected: stopword", stopword_found=result.stopword_found)
			raise DonationRejectedStopwordError()
		if result.verdict == "rejected_toxicity":
			log.info("ml.moderate rejected: toxicity", toxicity_score=result.toxicity_score)
			raise DonationRejectedToxicityError()

		log.debug("ml.moderate passed")

	async def synthesize_tts(
		self,
		text: str,
		donor_name: str,
		amount: int,
		voice: str,
		donation_id: int,
	) -> TTSResultDTO:
		log = logger.bind(
			request_donation_id=donation_id,
			request_donor_name=donor_name,
			request_amount=amount,
			request_voice=voice,
			request_text_length=len(text),
		)
		log.debug("ml.synthesize_tts started")

		result = await ml_gateway.synthesize_tts(
			self._client,
			TTSRequestDTO(
				text=text,
				donor_name=donor_name,
				amount=amount,
				voice=voice,
				donation_id=donation_id,
			),
		)
		log.info("ml.synthesize_tts done", audio_url=result.audio_url, duration_sec=result.duration_sec)
		return result
