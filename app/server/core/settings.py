from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from core.constants import CATALOG, OPENAI_DEFAULT_MODELS, ModelInfo

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _csv(name: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    raw = os.environ.get(name, "")
    if not raw.strip():
        return default
    return tuple(part.strip() for part in raw.split(",") if part.strip())


@dataclass(frozen=True)
class Settings:
    slot: str
    route: str
    residency: str
    max_usd: float
    default_model: str
    db_path: str
    api_key: str | None
    openai_key: str | None
    openai_base: str
    openai_models: tuple[str, ...]
    local_base: str | None
    local_key: str | None
    local_model: str
    jev_url: str | None
    demo: bool
    cors: tuple[str, ...]

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_key)

    @property
    def local_enabled(self) -> bool:
        return bool(self.local_base)

    def available_models(self) -> list[ModelInfo]:
        out: list[ModelInfo] = []
        if self.demo:
            out.extend([CATALOG["demo-small"], CATALOG["demo-frontier"]])
        if self.openai_enabled:
            for mid in self.openai_models:
                info = CATALOG.get(mid)
                if info is None:
                    info = ModelInfo(mid, "openai", "cloud", 0.01, 1.0, 4.0)
                out.append(info)
        if self.local_enabled:
            mid = self.local_model
            info = CATALOG.get(mid) or ModelInfo(mid, "local", "local", 0.0004, 0.0, 0.0)
            out.append(info)
        return out

    def model(self, model_id: str) -> ModelInfo | None:
        for info in self.available_models():
            if info.id == model_id:
                return info
        return None


def load_settings() -> Settings:
    openai_key = os.environ.get("OPENAI_API_KEY") or None
    local_base = os.environ.get("LOCAL_BASE_URL") or None
    real = bool(openai_key or local_base)
    demo_default = not real
    return Settings(
        slot=os.environ.get("RIVET_SLOT", "rules"),
        route=os.environ.get("RIVET_ROUTE", "cascade"),
        residency=os.environ.get("RIVET_RESIDENCY", "any"),
        max_usd=float(os.environ.get("RIVET_MAX_USD", "0.05")),
        default_model=os.environ.get("RIVET_DEFAULT_MODEL", "auto"),
        db_path=os.environ.get("RIVET_DB_PATH", "db/rivet.sqlite"),
        api_key=os.environ.get("RIVET_API_KEY") or None,
        openai_key=openai_key,
        openai_base=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        openai_models=_csv("RIVET_OPENAI_MODELS", OPENAI_DEFAULT_MODELS),
        local_base=local_base,
        local_key=os.environ.get("LOCAL_API_KEY") or None,
        local_model=os.environ.get("RIVET_LOCAL_MODEL", "local-llama"),
        jev_url=os.environ.get("JEV_URL") or None,
        demo=_bool("RIVET_DEMO", demo_default),
        cors=_csv(
            "RIVET_CORS",
            ("http://localhost:5173", "http://127.0.0.1:5173"),
        ),
    )
