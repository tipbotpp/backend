from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ModerationRequestDTO:
	text: str
	streamer_id: int
	stopwords: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ModerationResultDTO:
	is_toxic: bool
	toxicity_score: float
	stopword_found: str | None
	verdict: str  # "ok" | "rejected_toxicity" | "rejected_stopword"


@dataclass(slots=True)
class TTSRequestDTO:
	text: str
	donor_name: str
	amount: int
	voice: str
	donation_id: int


@dataclass(slots=True)
class TTSResultDTO:
	audio_key: str
	duration_sec: float
	donation_id: int


@dataclass(slots=True)
class ImageRequestDTO:
	text: str
	donor_name: str
	amount: int
	donation_id: int
	style_hint: str = "bright, celebration, coins"
	width: int = 512
	height: int = 512


@dataclass(slots=True)
class ImageResultDTO:
	image_key: str
	donation_id: int
