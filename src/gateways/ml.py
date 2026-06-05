import httpx

from src.schemas.dataclasses.ml import (
	ImageRequestDTO,
	ImageResultDTO,
	ModerationRequestDTO,
	ModerationResultDTO,
	TTSRequestDTO,
	TTSResultDTO,
)
from src.services.logger import get_logger

logger = get_logger().bind(layer="gateway", module="ml")


async def check_moderation(client: httpx.AsyncClient, dto: ModerationRequestDTO) -> ModerationResultDTO:
	log = logger.bind(
		request_streamer_id=dto.streamer_id,
		request_stopwords_count=len(dto.stopwords),
		request_text_length=len(dto.text),
	)
	log.debug("gateway.check_moderation request")

	response = await client.post(
		"/moderation/check",
		json={"text": dto.text, "stopwords": dto.stopwords, "streamer_id": dto.streamer_id},
	)
	response.raise_for_status()
	data = response.json()

	result = ModerationResultDTO(
		is_toxic=data["is_toxic"],
		toxicity_score=data["toxicity_score"],
		stopword_found=data.get("stopword_found"),
		verdict=data["verdict"],
	)
	log.debug("gateway.check_moderation response", verdict=result.verdict, status_code=response.status_code)
	return result


async def synthesize_tts(client: httpx.AsyncClient, dto: TTSRequestDTO) -> TTSResultDTO:
	log = logger.bind(
		request_donation_id=dto.donation_id,
		request_donor_name=dto.donor_name,
		request_amount=dto.amount,
		request_voice=dto.voice,
		request_text_length=len(dto.text),
	)
	log.debug("gateway.synthesize_tts request")

	response = await client.post(
		"/tts/synthesize",
		json={
			"text": dto.text,
			"donor_name": dto.donor_name,
			"amount": dto.amount,
			"voice": dto.voice,
			"donation_id": dto.donation_id,
		},
	)
	response.raise_for_status()
	data = response.json()

	result = TTSResultDTO(
		audio_key=data["audio_key"],
		duration_sec=data["duration_sec"],
		donation_id=data["donation_id"],
	)
	log.debug("gateway.synthesize_tts response", audio_key=result.audio_key, status_code=response.status_code)
	return result


async def generate_image(client: httpx.AsyncClient, dto: ImageRequestDTO) -> ImageResultDTO:
	log = logger.bind(
		request_donation_id=dto.donation_id,
		request_donor_name=dto.donor_name,
		request_amount=dto.amount,
		request_text_length=len(dto.text),
	)
	log.debug("gateway.generate_image request")

	response = await client.post(
		"/image/generate",
		json={
			"text": dto.text,
			"donor_name": dto.donor_name,
			"amount": dto.amount,
			"donation_id": dto.donation_id,
			"width": dto.width,
			"height": dto.height,
		},
	)
	response.raise_for_status()
	data = response.json()

	result = ImageResultDTO(
		image_key=data["image_key"],
		donation_id=data["donation_id"],
	)
	log.debug("gateway.generate_image response", image_key=result.image_key, status_code=response.status_code)
	return result
