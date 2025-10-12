import os
from functools import lru_cache
from typing import Optional

from pydantic import BaseModel
from dotenv import load_dotenv


class Settings(BaseModel):
    llm_provider: Optional[str] = None
    llm_api_key: Optional[str] = None
    model_name: Optional[str] = None
    google_api_key: Optional[str] = None
    gemini_model: Optional[str] = None

    # Azure OpenAI settings
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_deployment_name: Optional[str] = None
    azure_openai_api_version: Optional[str] = None
    azure_openai_model_name: Optional[str] = None
    azure_openai_fallback_deployment_name: Optional[str] = None
    azure_openai_fallback_api_version: Optional[str] = None

def get_settings() -> Settings:
    # Cargar variables desde .env si existe
    load_dotenv()
    return Settings(
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_openai_deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
        azure_openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_openai_model_name=os.getenv("AZURE_OPENAI_MODEL_NAME"),
        azure_openai_fallback_deployment_name=os.getenv("AZURE_OPENAI_FALLBACK_DEPLOYMENT_NAME"),
        azure_openai_fallback_api_version=os.getenv("AZURE_OPENAI_FALLBACK_API_VERSION"),
    )
