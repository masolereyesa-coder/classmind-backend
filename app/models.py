from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SubjectCreate(BaseModel):
    name: str
    professor_name: Optional[str] = None

class SubjectResponse(BaseModel):
    id: str
    name: str
    professor_name: Optional[str] = None
    user_id: str
    created_at: Optional[str] = None

class NoteResponse(BaseModel):
    id: str
    subject_id: str
    subject_name: str
    title: str
    transcript: str
    structured_notes: str
    qa_pairs: Optional[List[dict]] = []
    created_at: Optional[str] = None
    duration_seconds: Optional[int] = None

class AudioProcessRequest(BaseModel):
    subject_id: str
    user_id: str

class QARequest(BaseModel):
    question: str
    subject_id: str
    user_id: Optional[str] = None  # FIX: extraído del token, no requerido

class QAResponse(BaseModel):
    answer: str
    sources: List[str] = []

class UserCreate(BaseModel):
    email: str
    password: str
    name: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    token: str
    user_id: str
    email: str
    name: str
    refresh_token: Optional[str] = None  # FIX: para renovar tokens

class RefreshRequest(BaseModel):
    refresh_token: str

class NoteUpdateRequest(BaseModel):
    structured_notes: str
