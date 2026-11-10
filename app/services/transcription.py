from faster_whisper import WhisperModel
from app.config import settings
import asyncio
from typing import Tuple

# Modelo se carga una sola vez al iniciar
_model = None

def get_model():
    global _model
    if _model is None:
        _model = WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")
    return _model

async def transcribe_audio(audio_path: str) -> Tuple[str, int]:
    """
    Transcribe un archivo de audio y retorna (texto, duración_en_segundos)
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _transcribe_sync, audio_path)
    return result

def _transcribe_sync(audio_path: str) -> Tuple[str, int]:
    model = get_model()
    segments, info = model.transcribe(
        audio_path,
        language="es",
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    full_text = ""
    last_end = 0
    for segment in segments:
        full_text += segment.text + " "
        last_end = int(segment.end)

    return full_text.strip(), last_end
