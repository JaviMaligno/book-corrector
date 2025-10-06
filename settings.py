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

    # FDC (USDA FoodData Central) settings
    fdc_api_key: Optional[str] = None
    fdc_enabled: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Cargar variables desde .env si existe
    load_dotenv()
    return Settings(
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )
