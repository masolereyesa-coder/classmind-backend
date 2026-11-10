from groq import Groq
from app.config import settings
from typing import Optional

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client


async def generate_notes(
    transcript: str,
    subject_name: str,
    pdf_content: Optional[str] = None
) -> str:
    """
    Genera notas estructuradas a partir del transcript de clase.
    Si se proporciona pdf_content (texto extraído del PDF de la clase),
    la IA combina ambas fuentes para notas más completas.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, _generate_sync, transcript, subject_name, pdf_content
    )


def _generate_sync(
    transcript: str,
    subject_name: str,
    pdf_content: Optional[str]
) -> str:
    client = get_client()

    if pdf_content and len(pdf_content.strip()) > 50:
        # ── Modo enriquecido: audio + presentación PDF ──────────────────────
        prompt = f"""Eres un asistente académico experto. Tienes acceso a DOS fuentes de la misma clase de {subject_name}:
1. El material/presentación de la clase (extraído del PDF)
2. La transcripción del audio grabado en clase

Tu tarea es generar notas SUPERIORES combinando ambas fuentes:
- El PDF tiene los conceptos formales, definiciones exactas y estructura temática
- El audio tiene las explicaciones del profesor, ejemplos y énfasis real

MATERIAL DE LA CLASE (PDF):
{pdf_content[:4000]}

TRANSCRIPCIÓN DEL AUDIO:
{transcript[:5000]}

Genera notas integradas y completas con este formato EXACTO:

# Notas de Clase — {subject_name}

## Tema Principal
[El tema central, integrando título del PDF y lo que explicó el profesor]

## Conceptos Clave
- **[Concepto 1]**: [Definición formal del PDF + explicación del profesor si aplica]
- **[Concepto 2]**: [ídem]
- [Continúa con TODOS los conceptos importantes de ambas fuentes]

## Desarrollo del Contenido
[Explicación detallada combinando la estructura del PDF con las aclaraciones del audio. Párrafos organizados.]

## Ejemplos y Casos Prácticos
[Ejemplos del PDF y/o mencionados por el profesor en clase]

## Puntos Importantes a Recordar
- [Punto enfatizado en clase o destacado en el PDF]
- [Continúa...]

## Posibles Preguntas de Examen
1. [Basada en conceptos clave del PDF]
2. [Basada en énfasis del profesor en el audio]
3. [Continúa...]

Responde SOLO con las notas, sin texto adicional."""
    else:
        # ── Modo estándar: solo audio ────────────────────────────────────────
        prompt = f"""Eres un asistente académico experto. Analiza la siguiente transcripción de una clase de {subject_name} y genera notas estructuradas y completas.

TRANSCRIPCIÓN:
{transcript[:8000]}

Genera notas con este formato exacto:
# Resumen de la Clase

## Tema Principal
[El tema central de la clase en 1-2 oraciones]

## Conceptos Clave
- **[Concepto 1]**: [Explicación breve]
- **[Concepto 2]**: [Explicación breve]
- [Continúa con todos los conceptos importantes]

## Desarrollo del Contenido
[Explicación detallada de los temas vistos, en párrafos organizados]

## Ejemplos y Casos Prácticos
[Ejemplos mencionados en clase]

## Puntos Importantes a Recordar
- [Punto 1]
- [Punto 2]
- [Continúa...]

## Posibles Preguntas de Examen
1. [Pregunta probable 1]
2. [Pregunta probable 2]
3. [Continúa...]

Responde SOLO con las notas, sin texto adicional."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2500,
        temperature=0.3
    )

    return response.choices[0].message.content


async def answer_question(question: str, context: str) -> str:
    """
    Responde una pregunta usando las notas de la materia como contexto.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _answer_sync, question, context)


def _answer_sync(question: str, context: str) -> str:
    client = get_client()

    prompt = f"""Eres un asistente académico. Usando ÚNICAMENTE el contenido de las siguientes notas de clase, responde la pregunta del estudiante de forma clara y detallada.

NOTAS DE CLASE:
{context[:6000]}

PREGUNTA DEL ESTUDIANTE:
{question}

Si la respuesta no está en las notas, dilo claramente. Responde en español."""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.3
    )

    return response.choices[0].message.content
