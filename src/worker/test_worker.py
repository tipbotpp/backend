import asyncio
from types import SimpleNamespace

from worker.tasks.donations import process_donation_media


# --- MOCKS ---

class FakeSession:
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass

    async def begin(self):
        return self

class FakeSessionFactory:
    def __call__(self):
        return FakeSession()


class FakeBot:
    async def send_message(self, chat_id, text):
        print(f"[TELEGRAM] -> {chat_id}: {text}")


class FakeMLResult:
    def __init__(self):
        self.audio_key = "audio_test.mp3"
        self.image_key = "image_test.png"


# --- PATCH ML ---
async def fake_tts(*args, **kwargs):
    print("TTS called")
    return FakeMLResult()

async def fake_image(*args, **kwargs):
    print("IMAGE called")
    return FakeMLResult()


# --- TEST RUN ---
async def main():
    ctx = {
        "session_factory": FakeSessionFactory(),
        "ml_client": None,
        "bot": FakeBot(),
    }

    # monkey patch
    import src.gateways.ml as ml_gateway
    ml_gateway.synthesize_tts = fake_tts
    ml_gateway.generate_image = fake_image

    await process_donation_media(
        ctx,
        donation_id=1,
        text="Hello world",
        donor_name="Tester",
        amount=100,
        voice="test",
        tts_enabled=True,
        image_enabled=True,
        streamer_id=123,
    )


asyncio.run(main())