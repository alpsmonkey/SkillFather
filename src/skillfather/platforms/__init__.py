"""Multi-platform adapter registry for SkillFather.

Supports parsing skills from different Agent platforms:
- WorkBuddy (SKILL.md with YAML frontmatter)
- CodeBuddy (SKILL.md, same format as WorkBuddy)
- Codex / OpenAI Agent (SKILL.md + agents/openai.yaml)
- Claude Code (.claude/commands/*.md)
- Coze (visual platform, JSON export / .skill files)
- Hermes Agent (SKILL.md with Hermes-specific frontmatter)
"""

from skillfather.platforms.base import PlatformAdapter, PlatformInfo, register_platform
from skillfather.platforms.workbuddy import WorkBuddyAdapter
from skillfather.platforms.codebuddy import CodeBuddyAdapter
from skillfather.platforms.codex import CodexAdapter
from skillfather.platforms.claude_code import ClaudeCodeAdapter
from skillfather.platforms.coze import CozeAdapter
from skillfather.platforms.hermes import HermesAdapter

# All supported platforms
PLATFORMS = {
    "workbuddy": WorkBuddyAdapter,
    "codebuddy": CodeBuddyAdapter,
    "codex": CodexAdapter,
    "claude-code": ClaudeCodeAdapter,
    "coze": CozeAdapter,
    "hermes": HermesAdapter,
}


def get_platform(name: str) -> PlatformAdapter:
    """Get a platform adapter by name.

    Args:
        name: Platform name (e.g. 'workbuddy', 'codex', 'claude-code').

    Returns:
        PlatformAdapter instance.

    Raises:
        ValueError: If the platform is not supported.
    """
    name_lower = name.lower().replace("_", "-").replace(" ", "-")
    if name_lower in PLATFORMS:
        return PLATFORMS[name_lower]()
    if name_lower in ("openai", "openai-codex"):
        return PLATFORMS["codex"]()
    if name_lower in ("claude", "anthropic"):
        return PLATFORMS["claude-code"]()
    if name_lower in ("hermes-agent",):
        return PLATFORMS["hermes"]()

    available = ", ".join(sorted(PLATFORMS.keys()))
    raise ValueError(
        f"Unsupported platform: '{name}'. "
        f"Supported platforms: {available}"
    )


def list_platforms() -> list[PlatformInfo]:
    """List all supported platforms with their metadata."""
    return [adapter_cls().info() for adapter_cls in PLATFORMS.values()]


def detect_platform(path: str) -> PlatformAdapter | None:
    """Auto-detect the platform from file/directory structure.

    Args:
        path: Path to a skill file or directory.

    Returns:
        PlatformAdapter if detected, None otherwise.
    """
    from pathlib import Path

    p = Path(path)

    # Claude Code: .claude/commands/*.md
    parts = p.parts
    if ".claude" in parts and "commands" in parts and p.suffix == ".md":
        return ClaudeCodeAdapter()

    # Coze: .skill or .zip files
    if p.suffix == ".skill" or p.suffix == ".zip":
        return CozeAdapter()

    # Hermes: SKILL.md with hermes-specific fields
    if p.name == "SKILL.md":
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            if "metadata:" in content and "hermes:" in content:
                return HermesAdapter()
            if "agents/openai.yaml" in content.lower() or "allow_implicit_invocation" in content:
                return CodexAdapter()
            # Default to WorkBuddy/CodeBuddy (same format)
            # Check parent directory name for clues
            parent = str(p.parent)
            if ".codebuddy" in parent or ".workbuddy" in parent:
                if ".codebuddy" in parent:
                    return CodeBuddyAdapter()
                return WorkBuddyAdapter()
        except Exception:
            pass

    # Directory detection
    if p.is_dir():
        if (p / "SKILL.md").exists():
            try:
                content = (p / "SKILL.md").read_text(encoding="utf-8", errors="ignore")
                if "metadata:" in content and "hermes:" in content:
                    return HermesAdapter()
                if (p / "agents" / "openai.yaml").exists():
                    return CodexAdapter()
            except Exception:
                pass
            return WorkBuddyAdapter()
        if (p / ".claude" / "commands").is_dir():
            return ClaudeCodeAdapter()

    return None


def parse_skill_file(path: str, platform: str | None = None) -> "SkillProfile":
    """Parse a skill file using the specified or auto-detected platform.

    Args:
        path: Path to the skill file or directory.
        platform: Optional platform name. If None, auto-detect.

    Returns:
        SkillProfile with extracted information.
    """
    from skillfather.parser import SkillProfile

    if platform:
        adapter = get_platform(platform)
    else:
        adapter = detect_platform(path)

    if adapter is None:
        # Fallback: try generic SKILL.md parsing (WorkBuddy style)
        adapter = WorkBuddyAdapter()

    return adapter.parse(path)
