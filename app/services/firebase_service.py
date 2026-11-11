import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.config import settings
from datetime import datetime
from typing import Optional, List
import httpx
import base64
import json
import os

# Inicializar Firebase una sola vez
_db = None

def _get_firebase_credentials():
    """Obtiene credenciales desde base64 (Render) o desde archivo (local)."""
    if settings.firebase_credentials_base64:
        cred_json = base64.b64decode(settings.firebase_credentials_base64).decode('utf-8')
        cred_dict = json.loads(cred_json)
        return credentials.Certificate(cred_dict)
    return credentials.Certificate(settings.firebase_credentials_path)

def _initialize_firebase():
    """Inicializa Firebase Admin SDK si no ha sido inicializado."""
    if not firebase_admin._apps:
        cred = _get_firebase_credentials()
        firebase_admin.initialize_app(cred)

def get_db():
    global _db
    _initialize_firebase()
    if _db is None:
        _db = firestore.client()
    return _db

# Inicializar al importar el módulo
try:
    _initialize_firebase()
except Exception as e:
    import logging
    logging.warning(f"Firebase init deferred: {e}")

# ─── AUTH ────────────────────────────────────────────────────────────────────

async def verify_token(token: str) -> Optional[str]:
    """Verifica un token de Firebase y retorna el user_id."""
    try:
        _initialize_firebase()
        decoded = auth.verify_id_token(token)
        return decoded["uid"]
    except Exception:
        return None


async def _firebase_login(email: str, password: str) -> dict:
    """Login usando Firebase Auth REST API. Retorna idToken, refreshToken, etc."""
    api_key = settings.firebase_web_api_key
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={"email": email, "password": password, "returnSecureToken": True}
        )
        if response.status_code != 200:
            raise Exception("Credenciales inválidas")
        return response.json()


async def create_user(email: str, password: str, name: str) -> dict:
    """Crea usuario en Firebase Auth, guarda perfil en Firestore y retorna ID token real."""
    _initialize_firebase()
    user = auth.create_user(email=email, password=password, display_name=name)
    db = get_db()
    db.collection("users").document(user.uid).set({
        "name": name,
        "email": email,
        "created_at": datetime.utcnow().isoformat()
    })
    # FIX: usar REST API para obtener ID token real (no custom token)
    data = await _firebase_login(email, password)
    return {
        "token": data["idToken"],
        "refresh_token": data["refreshToken"],
        "user_id": data["localId"],
        "name": data.get("displayName", name),
        "email": email,
    }


async def login_user(email: str, password: str) -> dict:
    """Login usando Firebase Auth REST API. Retorna ID token + refresh token."""
    data = await _firebase_login(email, password)
    return {
        "token": data["idToken"],
        "refresh_token": data["refreshToken"],   # FIX: incluir refresh token
        "user_id": data["localId"],
        "name": data.get("displayName", ""),
        "email": email,
    }


async def refresh_id_token(refresh_token: str) -> dict:
    """Renueva el ID token usando el refresh token."""
    api_key = settings.firebase_web_api_key
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://securetoken.googleapis.com/v1/token?key={api_key}",
            data={"grant_type": "refresh_token", "refresh_token": refresh_token}
        )
        if response.status_code != 200:
            raise Exception("Refresh token inválido o expirado")
        data = response.json()
        return {
            "token": data["id_token"],
            "refresh_token": data["refresh_token"],
            "user_id": data["user_id"],
        }

# ─── SUBJECTS ────────────────────────────────────────────────────────────────

async def create_subject(user_id: str, name: str, professor_name: Optional[str] = None) -> str:
    db = get_db()
    doc_ref = db.collection("users").document(user_id).collection("subjects").document()
    doc_ref.set({
        "name": name,
        "professor_name": professor_name or "",
        "created_at": datetime.utcnow().isoformat(),
        "pdf_content": "",
        "pdf_filename": "",
    })
    return doc_ref.id

async def get_subjects(user_id: str) -> List[dict]:
    db = get_db()
    docs = db.collection("users").document(user_id).collection("subjects").stream()
    result = []
    for doc in docs:
        d = doc.to_dict()
        result.append({
            "id": doc.id,
            "name": d.get("name", ""),
            "professor_name": d.get("professor_name", ""),
            "created_at": d.get("created_at", ""),
            "pdf_filename": d.get("pdf_filename", ""),
        })
    return result

async def get_subject(subject_id: str, user_id: str) -> Optional[dict]:
    db = get_db()
    doc = db.collection("users").document(user_id).collection("subjects").document(subject_id).get()
    if doc.exists:
        d = doc.to_dict()
        return {"id": doc.id, **d}
    return None

async def delete_subject(subject_id: str, user_id: str):
    db = get_db()
    db.collection("users").document(user_id).collection("subjects").document(subject_id).delete()

async def save_subject_pdf(subject_id: str, user_id: str, pdf_text: str, filename: str) -> None:
    db = get_db()
    db.collection("users").document(user_id).collection("subjects").document(subject_id).update({
        "pdf_content": pdf_text,
        "pdf_filename": filename,
        "pdf_uploaded_at": datetime.utcnow().isoformat(),
    })

async def delete_subject_pdf(subject_id: str, user_id: str) -> None:
    db = get_db()
    db.collection("users").document(user_id).collection("subjects").document(subject_id).update({
        "pdf_content": "",
        "pdf_filename": "",
        "pdf_uploaded_at": "",
    })

# ─── NOTES ───────────────────────────────────────────────────────────────────

async def save_note(user_id: str, subject_id: str, subject_name: str,
                    transcript: str, structured_notes: str, duration: int) -> str:
    db = get_db()
    doc_ref = db.collection("users").document(user_id).collection("notes").document()
    created_at = datetime.utcnow().isoformat()
    doc_ref.set({
        "subject_id": subject_id,
        "subject_name": subject_name,
        "transcript": transcript,
        "structured_notes": structured_notes,
        "duration_seconds": duration,
        "qa_pairs": [],
        "created_at": created_at,
    })
    return doc_ref.id

async def get_notes(user_id: str) -> List[dict]:
    db = get_db()
    docs = (
        db.collection("users").document(user_id).collection("notes")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

async def get_notes_by_subject(subject_id: str, user_id: str, limit: int = 10) -> List[dict]:
    db = get_db()
    docs = (
        db.collection("users").document(user_id).collection("notes")
        .where("subject_id", "==", subject_id)
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

async def get_note(note_id: str, user_id: str) -> Optional[dict]:
    db = get_db()
    doc = db.collection("users").document(user_id).collection("notes").document(note_id).get()
    if doc.exists:
        return {"id": doc.id, **doc.to_dict()}
    return None

async def delete_note(note_id: str, user_id: str):
    db = get_db()
    db.collection("users").document(user_id).collection("notes").document(note_id).delete()

async def update_note_content(note_id: str, user_id: str, structured_notes: str) -> None:
    """FIX: Actualiza las notas estructuradas de una nota existente."""
    db = get_db()
    db.collection("users").document(user_id).collection("notes").document(note_id).update({
        "structured_notes": structured_notes,
        "edited_at": datetime.utcnow().isoformat(),
    })
