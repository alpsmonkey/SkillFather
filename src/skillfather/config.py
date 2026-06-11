"""Configuration management for SkillFather."""

import functools
import os
import json
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class LLMConfig:
    """LLM API configuration."""
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    max_tokens: int = 2048
    enabled: bool = False


@dataclass
class AnalysisConfig:
    """Analysis configuration."""
    num_questions: int = 8
    score_weights: dict[str, float] = field(default_factory=lambda: {
        "use_case": 0.25,       # 用例契合度
        "environment": 0.20,    # 环境就绪度
        "prerequisites": 0.20,  # 前置条件
        "workflow": 0.20,       # 工作流匹配
        "documentation": 0.15,  # 文档质量
    })


# All environment variable mappings in one place — eliminates duplicate reads
_ENV_MAPPING = {
    "SKILLFATHER_API_KEY": ("llm", "api_key"),
    "SKILLFATHER_BASE_URL": ("llm", "base_url"),
    "SKILLFATHER_MODEL": ("llm", "model"),
    "SKILLFATHER_NUM_QUESTIONS": ("analysis", "num_questions"),
    "OPENAI_API_KEY": ("llm", "api_key"),  # fallback key alias
}


@functools.lru_cache(maxsize=8)
def load_config(config_path: str | None = None) -> dict:
    """Load configuration from file and environment variables (cached).

    Priority: environment variables > config file > defaults.
    All env-var reads happen here — callers should not read os.environ directly.

    Results are cached by config_path string. Call clear_config_cache() to reset.
    """
    cfg: dict = {}

    # Load from config file if provided
    if config_path:
        p = Path(config_path)
        if p.exists():
            cfg = json.loads(p.read_text(encoding="utf-8"))

    # Environment variables override config file values (unified in one pass)
    for env_key, (section, key) in _ENV_MAPPING.items():
        value = os.environ.get(env_key)
        if value is not None:
            cfg.setdefault(section, {})[key] = value

    return cfg


def clear_config_cache() -> None:
    """Clear the load_config LRU cache (useful after env-var changes at runtime)."""
    load_config.cache_clear()


def get_llm_config(config_path: str | Path | None = None) -> LLMConfig:
    """Build LLMConfig from unified config (no duplicate env-var reads)."""
    cfg = load_config(str(config_path) if config_path else None)
    llm_cfg = cfg.get("llm", {})

    api_key = llm_cfg.get("api_key", "")

    return LLMConfig(
        api_key=api_key,
        base_url=llm_cfg.get("base_url", "https://api.openai.com/v1"),
        model=llm_cfg.get("model", "gpt-4o-mini"),
        enabled=bool(api_key),
    )


def _safe_int(raw, default: int = 8, lo: int = 1, hi: int = 50) -> int:
    """Safely convert a value to int with range clamping.

    Returns *default* on TypeError/ValueError; clamps result to [lo, hi].
    """
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, val))


def get_analysis_config(config_path: str | Path | None = None) -> AnalysisConfig:
    """Build AnalysisConfig from unified config (no duplicate env-var reads)."""
    cfg = load_config(str(config_path) if config_path else None)
    analysis_cfg = cfg.get("analysis", {})

    return AnalysisConfig(
        num_questions=_safe_int(analysis_cfg.get("num_questions"), default=8),
    )
