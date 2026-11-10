from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    groq_api_key: str
    huggingface_token: str = ""
    firebase_credentials_path: str = "firebase-credentials.json"
    firebase_credentials_base64: str = ""   # Base64 de firebase-credentials.json (para Render)
    firebase_project_id: str
    firebase_web_api_key: str = ""
    whisper_model: str = "base"
    secret_key: str = "classmind-secret-key-2024"

    class Config:
        env_file = ".env"

settings = Settings()
