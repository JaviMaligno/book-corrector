import os

from dotenv import load_dotenv
from pydantic import BaseModel


class Settings(BaseModel):
    llm_provider: str | None = None
    llm_api_key: str | None = None
    model_name: str | None = None
    google_api_key: str | None = None
    gemini_model: str | None = None

    # Azure OpenAI settings
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: str | None = None
    azure_openai_deployment_name: str | None = None
    azure_openai_api_version: str | None = None
    azure_openai_model_name: str | None = None
    azure_openai_fallback_deployment_name: str | None = None
    azure_openai_fallback_api_version: str | None = None


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
