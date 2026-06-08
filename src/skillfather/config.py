"""Configuration management for SkillFather."""

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
    score_weights: dict = field(default_factory=lambda: {
        "use_case": 0.25,       # 用例契合度
        "environment": 0.20,    # 环境就绪度
        "prerequisites": 0.20,  # 前置条件
        "workflow": 0.20,       # 工作流匹配
        "documentation": 0.15,  # 文档质量
    })


def load_config(config_path: str | Path | None = None) -> dict:
    """Load configuration from file or environment variables.

    Priority: config file > environment variables > defaults
    """
    cfg = {}

    # Load from config file if provided
    if config_path:
        p = Path(config_path)
        if p.exists():
            cfg = json.loads(p.read_text(encoding="utf-8"))

    # Environment variables override
    env_mapping = {
        "SKILLFATHER_API_KEY": ("llm", "api_key"),
        "SKILLFATHER_BASE_URL": ("llm", "base_url"),
        "SKILLFATHER_MODEL": ("llm", "model"),
        "SKILLFATHER_NUM_QUESTIONS": ("analysis", "num_questions"),
    }

    for env_key, (section, key) in env_mapping.items():
        value = os.environ.get(env_key)
        if value is not None:
            cfg.setdefault(section, {})[key] = value

    return cfg


def get_llm_config(config_path: str | Path | None = None) -> LLMConfig:
    """Build LLMConfig from config file and environment."""
    cfg = load_config(config_path)
    llm_cfg = cfg.get("llm", {})

    api_key = (
        os.environ.get("SKILLFATHER_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or llm_cfg.get("api_key", "")
    )

    return LLMConfig(
        api_key=api_key,
        base_url=os.environ.get("SKILLFATHER_BASE_URL") or llm_cfg.get("base_url", "https://api.openai.com/v1"),
        model=os.environ.get("SKILLFATHER_MODEL") or llm_cfg.get("model", "gpt-4o-mini"),
        enabled=bool(api_key),
    )


def get_analysis_config(config_path: str | Path | None = None) -> AnalysisConfig:
    """Build AnalysisConfig from config file and environment."""
    cfg = load_config(config_path)
    analysis_cfg = cfg.get("analysis", {})

    return AnalysisConfig(
        num_questions=int(
            os.environ.get("SKILLFATHER_NUM_QUESTIONS")
            or analysis_cfg.get("num_questions", 8)
        ),
    )
