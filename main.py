from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import audio, notes, subjects, auth
from app.config import settings

app = FastAPI(
    title="ClassMind API",
    description="Backend para transcripción y generación de notas de clases",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(audio.router, prefix="/api/v1", tags=["audio"])
app.include_router(notes.router, prefix="/api/v1", tags=["notes"])
app.include_router(subjects.router, prefix="/api/v1", tags=["subjects"])

@app.get("/")
async def root():
    return {"status": "ClassMind API running", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
