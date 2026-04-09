import httpx

from src.schemas.dataclasses.ml import (
	ModerationRequestDTO,
	ModerationResultDTO,
	TTSRequestDTO,
	TTSResultDTO,
)


async def check_moderation(client: httpx.AsyncClient, dto: ModerationRequestDTO) -> ModerationResultDTO:
	response = await client.post(
		"/moderation/check",
		json={"text": dto.text, "stopwords": dto.stopwords, "streamer_id": dto.streamer_id},
	)
	response.raise_for_status()
	data = response.json()
	return ModerationResultDTO(
		is_toxic=data["is_toxic"],
		toxicity_score=data["toxicity_score"],
		stopword_found=data.get("stopword_found"),
		verdict=data["verdict"],
	)


async def synthesize_tts(client: httpx.AsyncClient, dto: TTSRequestDTO) -> TTSResultDTO:
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
	return TTSResultDTO(
		audio_url=data["audio_url"],
		duration_sec=data["duration_sec"],
		donation_id=data["donation_id"],
	)
