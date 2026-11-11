import os
import asyncio
from typing import Tuple
from groq import Groq
from app.config import settings

_MAX_FILE_BYTES = 24 * 1024 * 1024  # 24 MB

# Extensiones válidas para Groq Whisper
_VALID_EXTENSIONS = {'.flac', '.mp3', '.mp4', '.mpeg', '.mpga', '.m4a', '.ogg', '.wav', '.webm'}

# Mapa de MIME types a extensiones
_MIME_TO_EXT = {
    'audio/mp4': '.m4a',
    'audio/m4a': '.m4a',
    'audio/aac': '.m4a',
    'audio/mpeg': '.mp3',
    'audio/mp3': '.mp3',
    'audio/ogg': '.ogg',
    'audio/wav': '.wav',
    'audio/x-wav': '.wav',
    'audio/flac': '.flac',
    'audio/webm': '.webm',
    'video/mp4': '.mp4',
    'video/webm': '.webm',
}


def _safe_extension(filename: str, content_type: str = "") -> str:
    """
    FIX: Determina una extensión válida para Groq Whisper.
    Prioridad: extensión del filename → content_type → fallback .m4a
    """
    if filename:
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if ext in _VALID_EXTENSIONS:
            return ext
    if content_type:
        ct = content_type.split(';')[0].strip().lower()
        mapped = _MIME_TO_EXT.get(ct)
        if mapped:
            return mapped
    return '.m4a'


async def transcribe_audio(audio_path: str, original_filename: str = "", content_type: str = "") -> Tuple[str, int]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _transcribe_sync, audio_path, original_filename, content_type
    )


def _transcribe_sync(audio_path: str, original_filename: str = "", content_type: str = "") -> Tuple[str, int]:
    file_size = os.path.getsize(audio_path)
    if file_size > _MAX_FILE_BYTES:
        size_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"El archivo de audio es demasiado grande ({size_mb:.0f} MB). "
            f"El límite es 24 MB. Graba desde la app (máx. 90 min) o usa un archivo más corto."
        )

    # FIX: usar nombre seguro con extensión válida para que Groq lo reconozca
    safe_ext = _safe_extension(original_filename or os.path.basename(audio_path), content_type)
    display_name = f"audio{safe_ext}"

    client = Groq(api_key=settings.groq_api_key)
    with open(audio_path, "rb") as f:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=(display_name, f),
            language="es",
            response_format="verbose_json",
        )
    duration = int(getattr(transcription, "duration", 0) or 0)
    text = getattr(transcription, "text", "") or ""
    return text.strip(), duration
