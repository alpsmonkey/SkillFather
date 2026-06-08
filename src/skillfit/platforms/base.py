"""Base class for platform adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import re

from skillfit.parser import SkillProfile


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


# Platform registry
_PLATFORM_REGISTRY: dict[str, type[PlatformAdapter]] = {}


def register_platform(name: str):
    """Decorator to register a platform adapter."""
    def decorator(cls):
        _PLATFORM_REGISTRY[name.lower()] = cls
        return cls
    return decorator


def _parse_yaml_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from content.

    Supports nested structures (metadata.hermes.tags), lists,
    multi-line scalars (>, |), and simple key-value pairs.

    Returns:
        (frontmatter_dict, body_text)
    """
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(pattern, content, re.DOTALL)
    if not match:
        return {}, content

    yaml_str = match.group(1)
    body = content[match.end():]

    lines = yaml_str.split("\n")
    unfolded = _unfold_multiline_scalars(lines)
    frontmatter = _parse_nested_yaml(unfolded)

    return frontmatter, body


def _unfold_multiline_scalars(lines: list[str]) -> list[str]:
    """Unfold YAML folded (>) and literal (|) block scalars."""
    result = []
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        fm_match = re.match(r"^(\S.*?)\s*:\s*[>|]\s*$", stripped)
        if fm_match:
            key = fm_match.group(1)
            is_literal = "|" in stripped
            value_lines = []
            i += 1
            while i < len(lines):
                next_stripped = lines[i].strip()
                if next_stripped == "":
                    if value_lines:
                        value_lines.append(" ")
                    i += 1
                    continue
                if next_stripped.startswith("- ") or next_stripped.startswith("#"):
                    break
                if not lines[i].startswith((" ", "\t")) and ":" in next_stripped:
                    break
                value_lines.append(next_stripped)
                i += 1
            if value_lines:
                sep = " " if not is_literal else "\n"
                result.append(f"{key}: {sep.join(v.strip() for v in value_lines)}")
            continue
        result.append(lines[i])
        i += 1
    return result


def _parse_nested_yaml(lines: list[str]) -> dict:
    """Parse unfolded YAML lines into a nested dictionary using indentation."""
    root: dict = {}
    # Stack: [(indent_level, dict_ref)]
    stack: list[tuple[int, dict]] = [(-1, root)]

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip())

        # Pop stack to find right parent level
        while len(stack) > 1 and stack[-1][0] >= indent:
            stack.pop()

        parent = stack[-1][1]

        if stripped.startswith("- "):
            # List item
            item_text = stripped[2:].strip()
            if ":" in item_text:
                ik, _, iv = item_text.partition(":")
                ik = ik.strip().strip("\"'")
                iv = iv.strip().strip("\"'")
                if iv.startswith("[") and iv.endswith("]"):
                    obj = [x.strip().strip("\"'-") for x in iv.strip("[]").split(",") if x.strip()]
                elif iv:
                    obj = iv
                else:
                    obj = {}
                parent.setdefault("_items", []).append({ik: obj})
            else:
                parent.setdefault("_items", []).append(item_text.strip("\"'-"))
            continue

        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip().strip("\"'")
            value = value.strip()

            if value.startswith("[") and value.endswith("]"):
                items = [x.strip().strip("\"'-") for x in value.strip("[]").split(",") if x.strip()]
                parent[key] = items
            elif value:
                parent[key] = value.strip("\"'")
            else:
                # Nested key - value is a dict
                new_dict: dict = {}
                parent[key] = new_dict
                stack.append((indent, new_dict))

    # Post-process _items into proper structures
    _post_process(root)
    return root


def _post_process(d: dict):
    """Convert _items markers into proper lists."""
    for key, val in list(d.items()):
        if isinstance(val, dict):
            _post_process(val)
            if "_items" in val:
                items = val.pop("_items")
                # Merge single-key dicts into parent
                merged: dict = {}
                for item in items:
                    if isinstance(item, dict):
                        merged.update(item)
                    else:
                        # Mixed list: has both dicts and strings
                        if not merged:
                            d[key] = items
                            return
                        d[key] = items
                        return
                if merged:
                    val.update(merged)
                elif items:
                    d[key] = items
