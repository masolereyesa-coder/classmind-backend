"""
Extrae texto de un PDF usando pypdf.
Ligero, sin dependencias pesadas, funciona en Render free tier.
"""
import io
from typing import Tuple

MAX_CHARS = 50_000  # límite para no saturar Firestore (~1MB/doc) ni el prompt


def extract_text_from_pdf(content: bytes) -> Tuple[str, int]:
    """
    Recibe el contenido binario de un PDF.
    Retorna (texto_extraido, num_paginas).
    El texto se trunca a MAX_CHARS si es muy largo.
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        raise RuntimeError("pypdf no está instalado. Agrega 'pypdf>=4.0.0' a requirements.txt")

    reader = PdfReader(io.BytesIO(content))
    pages = reader.pages
    num_pages = len(pages)

    parts = []
    for i, page in enumerate(pages):
        text = page.extract_text() or ""
        parts.append(f"[Pág. {i+1}]\n{text}")

    full_text = "\n\n".join(parts).strip()

    if len(full_text) > MAX_CHARS:
        full_text = full_text[:MAX_CHARS] + "\n\n[... texto truncado por longitud ...]"

    return full_text, num_pages
