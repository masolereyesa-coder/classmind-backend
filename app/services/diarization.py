# CLOUD VERSION: pyannote desactivado (requiere ~2GB RAM; Render gratis tiene 512MB)
# Para activar diarización localmente, restaurar el archivo diarization_local.py

async def diarize_audio(audio_path: str, transcript: str) -> str:
    """
    Versión cloud: retorna transcript sin etiquetar hablantes.
    La funcionalidad de transcripción, notas y Q&A sigue siendo 100% funcional.
    """
    return transcript
