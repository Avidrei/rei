import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "REI (Retrieval & Execution Interface)"
    # Completely free tier key from Google AI Studio
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Storage directory paths
    BASE_DIR: str = os.path.dirname(os.path.dirname(__file__))
    UPLOAD_DIR: str = os.path.join(BASE_DIR, "app", "storage", "uploads")
    FAISS_DIR: str = os.path.join(BASE_DIR, "app", "storage", "faiss_index")

settings = Settings()

# Ensure internal safe sandbox folders exist on instant launch
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.FAISS_DIR, exist_ok=True)