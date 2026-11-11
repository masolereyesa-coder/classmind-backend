from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import tempfile
import os
from datetime import datetime
from app.services.transcription import transcribe_audio
from app.services.diarization import diarize_audio
from app.services.notes_generator import generate_notes
from app.services.firebase_service import save_note, get_subject, verify_token

router = APIRouter()
security = HTTPBearer()


@router.post("/process-audio")
async def process_audio(
    audio_file: UploadFile = File(...),
    subject_id: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # Verificar token
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Verificar que la materia existe (también trae pdf_content si tiene)
    subject = await get_subject(subject_id, user_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Guardar audio temporalmente
    suffix = os.path.splitext(audio_file.filename)[1] if audio_file.filename else ".m4a"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        while True:
            chunk = await audio_file.read(1024 * 1024)  # 1 MB por chunk
            if not chunk:
                break
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        # Transcribir
        transcript, duration = await transcribe_audio(tmp_path)

        # Diarizar (en cloud retorna el mismo transcript)
        diarized_text = await diarize_audio(tmp_path, transcript)

        # Obtener contenido del PDF si existe
        pdf_content = subject.get("pdf_content", "") or ""

        # Generar notas estructuradas con IA (enriquecidas con PDF si hay)
        structured_notes = await generate_notes(
            transcript=diarized_text,
            subject_name=subject["name"],
            pdf_content=pdf_content if pdf_content.strip() else None
        )

        # Guardar en Firestore
        created_at = datetime.utcnow().isoformat()
        note_id = await save_note(
            user_id=user_id,
            subject_id=subject_id,
            subject_name=subject["name"],
            transcript=diarized_text,
            structured_notes=structured_notes,
            duration=duration
        )

        # Retornar todos los campos que Note.fromJson() espera
        return {
            "id": note_id,
            "subject_id": subject_id,
            "subject_name": subject["name"],
            "transcript": diarized_text,
            "structured_notes": structured_notes,
            "duration_seconds": duration,
            "created_at": created_at,
            "qa_pairs": [],
            "used_pdf": bool(pdf_content.strip()),
        }
    finally:
        # Borrar audio (nunca se almacena)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
