from groq import Groq
from app.config import settings

_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=settings.groq_api_key)
    return _client

async def generate_notes(transcript: str, subject_name: str) -> str:
    """
    Genera notas estructuradas a partir del transcript de clase.
    """
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _generate_sync, transcript, subject_name)

def _generate_sync(transcript: str, subject_name: str) -> str:
    client = get_client()

    prompt = f"""Eres un asistente académico experto. Analiza la siguiente transcripción de una clase de {subject_name} y genera notas estructuradas y completas.

TRANSCRIPCIÓN:
{transcript[:8000]}

Genera notas con este formato exacto:
# Resumen de la Clase

## Tema Principal
[El tema central de la clase en 1-2 oraciones]

## Conceptos Clave
- [Concepto 1]: [Explicación breve]
- [Concepto 2]: [Explicación breve]
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
        max_tokens=2000,
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
