from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import tempfile
import os
from app.services.transcription import transcribe_audio
from app.services.diarization import diarize_audio
from app.services.notes_generator import generate_notes
from app.services.firebase_service import save_note, get_subject, verify_token

router = APIRouter()
security = HTTPBearer()

@router.post("/process-audio")
async def process_audio(
    file: UploadFile = File(...),
    subject_id: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verificar token
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Verificar que la materia existe
    subject = await get_subject(subject_id, user_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Guardar audio temporalmente
    suffix = os.path.splitext(file.filename)[1] if file.filename else ".m4a"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Transcribir
        transcript, duration = await transcribe_audio(tmp_path)

        # Diarizar (identificar hablantes)
        diarized_text = await diarize_audio(tmp_path, transcript)

        # Generar notas estructuradas con IA
        structured_notes = await generate_notes(diarized_text, subject["name"])

        # Guardar en Firestore
        note_id = await save_note(
            user_id=user_id,
            subject_id=subject_id,
            subject_name=subject["name"],
            transcript=diarized_text,
            structured_notes=structured_notes,
            duration=duration
        )

        return {
            "success": True,
            "note_id": note_id,
            "transcript": diarized_text,
            "structured_notes": structured_notes,
            "duration_seconds": duration
        }
    finally:
        # Borrar audio (nunca se almacena)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
