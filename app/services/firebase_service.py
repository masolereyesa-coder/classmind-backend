import firebase_admin
from firebase_admin import credentials, firestore, auth
from app.config import settings
from datetime import datetime
from typing import Optional, List
import httpx
import base64
import json
import tempfile
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

def get_db():
    global _db
    if _db is None:
        if not firebase_admin._apps:
            cred = _get_firebase_credentials()
            firebase_admin.initialize_app(cred)
        _db = firestore.client()
    return _db

# ─── AUTH ────────────────────────────────────────────────────────────────────

async def verify_token(token: str) -> Optional[str]:
    """Verifica un token de Firebase y retorna el user_id."""
    try:
        decoded = auth.verify_id_token(token)
        return decoded["uid"]
    except Exception:
        return None

async def create_user(email: str, password: str, name: str) -> dict:
    """Crea un usuario en Firebase Auth y guarda su perfil en Firestore."""
    user = auth.create_user(email=email, password=password, display_name=name)
    db = get_db()
    db.collection("users").document(user.uid).set({
        "name": name,
        "email": email,
        "created_at": datetime.utcnow().isoformat()
    })
    # Generar token custom (el cliente debe canjearlo por ID token)
    custom_token = auth.create_custom_token(user.uid)
    return {"token": custom_token.decode(), "user_id": user.uid}

async def login_user(email: str, password: str) -> dict:
    """Login usando Firebase Auth REST API."""
    api_key = settings.firebase_web_api_key
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
            json={"email": email, "password": password, "returnSecureToken": True}
        )
        if response.status_code != 200:
            raise Exception("Credenciales inválidas")
        data = response.json()
        return {
            "token": data["idToken"],
            "user_id": data["localId"],
            "name": data.get("displayName", "")
        }

# ─── SUBJECTS ────────────────────────────────────────────────────────────────

async def create_subject(user_id: str, name: str, professor_name: Optional[str] = None) -> str:
    db = get_db()
    doc_ref = db.collection("users").document(user_id).collection("subjects").document()
    doc_ref.set({
        "name": name,
        "professor_name": professor_name or "",
        "created_at": datetime.utcnow().isoformat()
    })
    return doc_ref.id

async def get_subjects(user_id: str) -> List[dict]:
    db = get_db()
    docs = db.collection("users").document(user_id).collection("subjects").stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

async def get_subject(subject_id: str, user_id: str) -> Optional[dict]:
    db = get_db()
    doc = db.collection("users").document(user_id).collection("subjects").document(subject_id).get()
    if doc.exists:
        return {"id": doc.id, **doc.to_dict()}
    return None

async def delete_subject(subject_id: str, user_id: str):
    db = get_db()
    db.collection("users").document(user_id).collection("subjects").document(subject_id).delete()

# ─── NOTES ───────────────────────────────────────────────────────────────────

async def save_note(
    user_id: str,
    subject_id: str,
    subject_name: str,
    transcript: str,
    structured_notes: str,
    duration: int
) -> str:
    db = get_db()
    doc_ref = db.collection("users").document(user_id).collection("notes").document()
    doc_ref.set({
        "subject_id": subject_id,
        "subject_name": subject_name,
        "transcript": transcript,
        "structured_notes": structured_notes,
        "duration_seconds": duration,
        "qa_pairs": [],
        "created_at": datetime.utcnow().isoformat()
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
