from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import SubjectCreate, SubjectResponse
from app.services.firebase_service import (
    create_subject, get_subjects, get_subject,
    delete_subject, verify_token, save_subject_pdf, delete_subject_pdf
)
from app.services.pdf_extractor import extract_text_from_pdf

router = APIRouter()
security = HTTPBearer()

MAX_PDF_SIZE = 20 * 1024 * 1024  # 20 MB


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
        professor_name=subject.professor_name or "",
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
    # No exponer pdf_content en este endpoint
    subject.pop("pdf_content", None)
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


@router.post("/subjects/{subject_id}/pdf")
async def upload_subject_pdf(
    subject_id: str,
    pdf_file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Sube el PDF de la presentación/material de una materia.
    El texto extraído se guarda en Firestore y se usa para enriquecer las notas de audio.
    """
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Validar que la materia existe y pertenece al usuario
    subject = await get_subject(subject_id, user_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    # Validar que es un PDF
    filename = pdf_file.filename or "documento.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")

    # Leer contenido
    content = await pdf_file.read()
    if len(content) > MAX_PDF_SIZE:
        raise HTTPException(status_code=413, detail="El PDF no puede superar 20 MB")
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="El PDF está vacío")

    # Extraer texto
    try:
        pdf_text, num_pages = extract_text_from_pdf(content)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"No se pudo leer el PDF: {str(e)}")

    if not pdf_text.strip():
        raise HTTPException(
            status_code=422,
            detail="No se pudo extraer texto del PDF. Puede ser un PDF escaneado (imagen)."
        )

    # Guardar en Firestore
    await save_subject_pdf(subject_id, user_id, pdf_text, filename)

    return {
        "success": True,
        "filename": filename,
        "pages": num_pages,
        "chars_extracted": len(pdf_text),
    }


@router.delete("/subjects/{subject_id}/pdf")
async def remove_subject_pdf(
    subject_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Elimina el PDF de una materia."""
    user_id = await verify_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token inválido")

    subject = await get_subject(subject_id, user_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Materia no encontrada")

    await delete_subject_pdf(subject_id, user_id)
    return {"success": True}
