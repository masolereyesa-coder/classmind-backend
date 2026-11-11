import os
import asyncio
from typing import Tuple
from groq import Groq
from app.config import settings

_MAX_FILE_BYTES = 24 * 1024 * 1024  # 24 MB


async def transcribe_audio(audio_path: str) -> Tuple[str, int]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe_sync, audio_path)


def _transcribe_sync(audio_path: str) -> Tuple[str, int]:
    file_size = os.path.getsize(audio_path)
    if file_size > _MAX_FILE_BYTES:
        size_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"El archivo de audio es demasiado grande ({size_mb:.0f} MB). "
            f"El límite es 24 MB. Si grabas desde la app (grabadora integrada), "
            f"esto no debería ocurrir. Para archivos externos, usa uno más corto "
            f"o de menor calidad (máx. ~90 min en formato m4a/aac)."
        )
    client = Groq(api_key=settings.groq_api_key)
    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=(os.path.basename(audio_path), f),
            language="es",
            response_format="verbose_json",
        )
    duration = int(getattr(transcription, "duration", 0) or 0)
    text = getattr(transcription, "text", "") or ""
    return text.strip(), duration
