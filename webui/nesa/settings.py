from functools import lru_cache
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field
import os
import json

load_dotenv()

class Settings(BaseSettings):
    project_name: str = Field(default="default-service", description="Name of the project")
    version: str = Field(default="0.0.1", description="Current version of the service")
    publish_configs: Dict[str, Any] = Field(
        default_factory=dict, description="Generic publish configurations"
    )
    consume_configs: Dict[str, Any] = Field(
        default_factory=dict, description="Generic consume configurations"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        frozen = True
        extra = 'allow'

def load_configs(prefix: str) -> Dict[str, Any]:
    """
    load configurations based on the given prefix.
    """
    keys = [key for key in os.environ.keys() if key.startswith(f"{prefix}_")]
    configs = {}
    for key in keys:
        config_key = key.removeprefix(f"{prefix}_").lower()
        value = os.getenv(key)
        try:
            configs[config_key] = json.loads(value) if value.startswith("[") else value
        except json.JSONDecodeError:
            configs[config_key] = value
    return configs

@lru_cache
def get_settings() -> Settings:
    """
    retrieve the singleton instance of the application settings
    """
    settings = Settings()
    publish_configs = load_configs("PUBLISH")
    consume_configs = load_configs("CONSUME")
    return settings.model_copy(
        update={
            "publish_configs": publish_configs,
            "consume_configs": consume_configs,
        }
    )

settings = get_settings()