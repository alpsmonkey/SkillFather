"""Base class for platform adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from skillfather.parser import SkillProfile
from skillfather.yaml_utils import parse_yaml_frontmatter


@dataclass
class PlatformInfo:
    """Metadata about a supported platform."""

    name: str
    display_name: str
    description: str
    skill_format: str
    storage_paths: list[str]
    file_extensions: list[str]
    docs_url: str = ""


class PlatformAdapter(ABC):
    """Abstract base class for platform-specific skill parsers.

    Each platform adapter knows how to:
    1. Detect if a file/directory belongs to its platform
    2. Parse the platform-specific format into a unified SkillProfile
    3. Provide platform-specific analysis context
    """

    @abstractmethod
    def info(self) -> PlatformInfo:
        """Return metadata about this platform."""
        ...

    @abstractmethod
    def parse(self, path: str | Path) -> SkillProfile:
        """Parse a skill file/directory into a unified SkillProfile.

        Args:
            path: Path to skill file, SKILL.md, command .md, directory, or .skill archive.

        Returns:
            SkillProfile with all extracted information.
        """
        ...

    def detect(self, path: str | Path) -> bool:
        """Check if the given path belongs to this platform."""
        return False

    def get_platform_context(self, profile: SkillProfile) -> str:
        """Return platform-specific context for analysis."""
        info = self.info()
        return (
            f"平台: {info.display_name}\n"
            f"技能格式: {info.skill_format}\n"
            f"存储路径: {', '.join(info.storage_paths)}"
        )

    def get_platform_name(self) -> str:
        return self.info().name


# Re-export for backward compatibility with any code importing from this module
_parse_yaml_frontmatter = parse_yaml_frontmatter
