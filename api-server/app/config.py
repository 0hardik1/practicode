from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


CURRENT_FILE = Path(__file__).resolve()
DEFAULT_PROBLEMS_DIR = next(
    (
        candidate / "problems"
        for candidate in [CURRENT_FILE.parents[2], CURRENT_FILE.parents[1]]
        if (candidate / "problems").exists()
    ),
    CURRENT_FILE.parents[1] / "problems",
)


class Settings(BaseSettings):
    app_name: str = "PractiCode API"
    database_url: str = "sqlite+aiosqlite:///./practicode.db"
    executor_base_url: str = "http://localhost:8080"
    execution_environment: str = "local"
    problems_dir: Path = DEFAULT_PROBLEMS_DIR
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    model_config = SettingsConfigDict(
        env_prefix="PRACTICODE_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
