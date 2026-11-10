from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import QARequest, QAResponse
from app.services.firebase_service import get_notes, get_note, delete_note, verify_token, get_notes_by_subject
from app.services.notes_generator import answer_question

router = APIRouter()
security = HTTPBearer()

@router.get("/notes")
async def list_notes(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    notes = await get_notes(user_id)
    return {"notes": notes}

@router.get("/notes/{note_id}")
async def get_single_note(
    note_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    note = await get_note(note_id, user_id)
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return note

@router.delete("/notes/{note_id}")
async def remove_note(
    note_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    await delete_note(note_id, user_id)
    return {"success": True}

@router.post("/qa", response_model=QAResponse)
async def qa_endpoint(
    request: QARequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Obtener últimas 10 notas de la materia como contexto
    notes = await get_notes_by_subject(request.subject_id, user_id, limit=10)
    context = "\n\n".join([
        f"Clase del {n.get('created_at', 'fecha desconocida')}:\n{n.get('structured_notes', '')}"
        for n in notes
    ])

    answer = await answer_question(request.question, context)
    return QAResponse(answer=answer, sources=[n.get("id", "") for n in notes])
