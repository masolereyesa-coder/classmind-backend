from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import SubjectCreate, SubjectResponse
from app.services.firebase_service import (
    create_subject, get_subjects, get_subject,
    delete_subject, verify_token
)

router = APIRouter()
security = HTTPBearer()

@router.post("/subjects", response_model=SubjectResponse)
async def create_new_subject(
    subject: SubjectCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    subject_id = await create_subject(user_id, subject.name, subject.professor_name)
    return SubjectResponse(
        id=subject_id,
        name=subject.name,
        professor_name=subject.professor_name,
        user_id=user_id
    )

@router.get("/subjects")
async def list_subjects(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    subjects = await get_subjects(user_id)
    return {"subjects": subjects}

@router.get("/subjects/{subject_id}")
async def get_single_subject(
    subject_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    subject = await get_subject(subject_id, user_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")
    return subject

@router.delete("/subjects/{subject_id}")
async def remove_subject(
    subject_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    await delete_subject(subject_id, user_id)
    return {"success": True}
