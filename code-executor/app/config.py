from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


CURRENT_FILE = Path(__file__).resolve()
DEFAULT_REPO_ROOT = next(
    (candidate for candidate in [CURRENT_FILE.parents[2], CURRENT_FILE.parents[1]] if (candidate / "runner-python").exists()),
    CURRENT_FILE.parents[1],
)


class Settings(BaseSettings):
    app_name: str = "PractiCode Executor"
    execution_mode: str = "local"
    api_callback_url: str = "http://localhost:8000/api/internal/results"
    runner_python_bin: str = "python3"
    runner_path: Path = DEFAULT_REPO_ROOT / "runner-python" / "app" / "harness.py"

    model_config = SettingsConfigDict(
        env_prefix="PRACTICODE_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

