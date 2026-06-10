"""SKILL.md file parser - extracts structured information from WorkBuddy SKILL files."""

import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SkillProfile:
    """Structured representation of a parsed SKILL.md file."""

    path: str
    raw_content: str

    # Frontmatter
    name: str = ""
    summary: str = ""
    title: str = ""
    read_when: list[str] = field(default_factory=list)
    frontmatter_raw: dict[str, object] = field(default_factory=dict)

    # Content sections
    description: str = ""
    triggers: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)
    instructions: str = ""
    tools_required: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    all_sections: dict[str, str] = field(default_factory=dict)

    @property
    def display_name(self) -> str:
        return self.name or self.title or Path(self.path).stem

    @property
    def trigger_text(self) -> str:
        return "、".join(self.triggers[:8]) if self.triggers else "未检测到触发词"

    @property
    def requirement_text(self) -> str:
        return "、".join(self.requirements[:8]) if self.requirements else "未检测到前置条件"

    @property
    def tool_text(self) -> str:
        return "、".join(self.tools_required[:8]) if self.tools_required else "未检测到工具依赖"

    @property
    def capability_text(self) -> str:
        return "、".join(self.capabilities[:8]) if self.capabilities else "未检测到功能描述"


def parse_skill(path: str | Path) -> SkillProfile:
    """Parse a SKILL.md file and return a structured SkillProfile.

    Args:
        path: Path to the SKILL.md file.

    Returns:
        SkillProfile with extracted information.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SKILL.md not found: {path}")

    content = path.read_text(encoding="utf-8")
    profile = SkillProfile(path=str(path.resolve()), raw_content=content)

    _parse_frontmatter(content, profile)
    _parse_content(content, profile)

    # Derive name from frontmatter or first heading
    if not profile.name and not profile.title:
        heading_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
        if heading_match:
            profile.name = heading_match.group(1).strip()

    return profile


def _parse_frontmatter(content: str, profile: SkillProfile):
    """Extract YAML frontmatter from SKILL.md.

    Uses skillfather.yaml_utils which supports:
    - Simple key: value pairs
    - Inline lists [a, b, c]
    - Indented list items (- item)
    - Nested YAML (metadata.hermes.tags)
    - Multi-line scalars (>, |)
    """
    from skillfather.yaml_utils import parse_yaml_frontmatter

    fm, _ = parse_yaml_frontmatter(content)
    if not fm:
        return

    profile.frontmatter_raw = fm

    # Map common frontmatter fields (flatten top-level only)
    profile.name = (
        profile.frontmatter_raw.get("title", "")
        or profile.frontmatter_raw.get("name", "")
    )
    raw_summary = (
        profile.frontmatter_raw.get("summary", "")
        or profile.frontmatter_raw.get("description", "")
    )
    # Normalize to string (base.py may return list for multi-line values)
    if isinstance(raw_summary, list):
        raw_summary = " ".join(str(s) for s in raw_summary)
    # Normalize multi-line summary to single line
    profile.summary = re.sub(r"\s*\n\s*", " ", str(raw_summary)).strip()

    read_when = profile.frontmatter_raw.get("read_when", [])
    if isinstance(read_when, list):
        profile.read_when = read_when
    elif isinstance(read_when, str) and read_when.strip():
        profile.read_when = [item.strip() for item in read_when.strip("[]").split(",") if item.strip()]


def _parse_content(content: str, profile: SkillProfile):
    """Extract content sections from SKILL.md body."""
    # Remove frontmatter
    body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, count=1, flags=re.DOTALL)

    # Build sections map once and pass to all extractors
    sections = _build_sections_map(body)

    # Split into sections by headers — also populate all_sections
    for key, val in sections.items():
        profile.all_sections[key] = val

    # Extract specific dimensions — pass pre-built sections map
    _extract_triggers(body, profile, sections)
    _extract_requirements(body, profile, sections)
    _extract_capabilities(body, profile, sections)

    # Set full instructions
    profile.instructions = body
    # Description: summary or first non-heading paragraph
    if not profile.description:
        paragraphs = re.split(r"\n\n+", body)
        for p in paragraphs:
            clean = p.strip()
            # Skip heading lines
            if clean.startswith("#") or len(clean) < 20:
                continue
            # Strip markdown formatting for clean description
            clean = re.sub(r"[#*\-`>\[\]()]", "", clean).strip()
            if len(clean) >= 20:
                profile.description = clean[:200]
                break


def _build_sections_map(body: str) -> dict[str, str]:
    """Parse body into a {header: content} dict. Built once, reused by all extractors."""
    sections: dict[str, str] = {}
    parts = re.split(r"^(#{1,4}\s+.+)$", body, flags=re.MULTILINE)
    for i in range(1, len(parts), 2):
        header = re.sub(r"^#+\s*", "", parts[i].strip())
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections[header] = content
    return sections


def _extract_triggers(body: str, profile: SkillProfile, sections: dict[str, str] | None = None):
    """Extract trigger phrases from the skill content.

    Handles multiple common formats:
    - "## 触发条件" with list items
    - "触发词：" inline
    - "当用户...时，使用此技能"
    - "适用场景："
    - Frontmatter summary containing trigger keywords
    """
    # Pattern 1: ## 触发条件 section with list items
    trigger_section = _get_section_text(body, ["触发条件", "触发词", "Triggers", "触发场景"], sections)

    if trigger_section:
        # Extract list items (- xxx)
        list_items = re.findall(r"[-•]\s*(.+)", trigger_section)
        for item in list_items:
            # Split comma-separated items within a list line
            sub_items = re.split(r"[,，、;；]", item.strip())
            profile.triggers.extend(s.strip() for s in sub_items if s.strip())

        # Also extract "当用户提及...时" pattern
        intro_matches = re.findall(r"当用户(?:提及|提问|涉及).*?[:：]?\n?", trigger_section)
        for m in intro_matches:
            profile.triggers.append(m.strip())

    # Pattern 2: inline trigger patterns
    inline_patterns = [
        r"(?:触发(?:词|条件)：?\s*)([^\n]+)",
        r"(?:适用场景[：:]?\s*)([^\n]+)",
    ]
    for pattern in inline_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        for match in matches:
            items = re.split(r"[,，、;；]", match.strip())
            profile.triggers.extend(item.strip() for item in items if item.strip())

    # Pattern 3: from frontmatter summary/description containing "触发词："
    if profile.summary:
        trigger_kw_match = re.search(r"触发词[：:]\s*(.+)", profile.summary)
        if trigger_kw_match:
            kw_str = trigger_kw_match.group(1)
            items = re.split(r"[,，、;；]", kw_str.strip())
            # Prepend frontmatter triggers (more authoritative)
            fm_triggers = [item.strip() for item in items if item.strip() and len(item.strip()) >= 2]
            profile.triggers = fm_triggers + profile.triggers

    _deduplicate(profile.triggers, min_len=2)


def _extract_requirements(body: str, profile: SkillProfile, sections: dict[str, str] | None = None):
    """Extract requirements and prerequisites from the skill content."""
    req_section = _get_section_text(body, ["前置条件", "前提条件", "Prerequisites", "Requirements"], sections)

    if req_section:
        list_items = re.findall(r"[-•]\s*(.+)", req_section)
        for item in list_items:
            profile.requirements.append(item.strip())

    # Also look for inline patterns
    req_patterns = [
        r"(?:前置条件|前提条件)(?:[：:]?\s*)([^\n]+)",
    ]
    for pattern in req_patterns:
        matches = re.findall(pattern, body, re.IGNORECASE)
        for match in matches:
            profile.requirements.append(match.strip())

    # Extract MCP tools with more robust patterns
    _extract_mcp_tools(body, profile)

    # Extract explicit tool/dependency references
    _extract_dependencies(body, profile, sections)

    _deduplicate(profile.requirements, min_len=2)
    _deduplicate(profile.tools_required, min_len=2)


def _extract_mcp_tools(body: str, profile: SkillProfile):
    """Extract MCP tool references from skill content."""
    # Pattern 1: bare mcp__xxx references (not in backticks)
    bare_mcp = re.findall(r"(mcp__[a-zA-Z0-9_-]+)", body)
    # Pattern 2: backtick-wrapped `mcp__xxx`
    ticked_mcp = re.findall(r"`(mcp__[a-zA-Z0-9_-]+)`", body)

    all_mcp = bare_mcp + ticked_mcp
    seen = set()
    for tool in all_mcp:
        if tool not in seen:
            seen.add(tool)
            profile.tools_required.append(tool)


def _extract_dependencies(body: str, profile: SkillProfile, sections: dict[str, str] | None = None):
    """Extract explicit dependency references."""
    dep_section = _get_section_text(body, ["依赖", "Dependencies", "工具依赖", "知识库配置"], sections)

    if dep_section:
        # Extract list items (- xxx) from the section
        list_items = re.findall(r"[-•]\s*(.+)", dep_section)
        for item in list_items:
            cleaned = item.strip().strip("`'\"")
            if len(cleaned) >= 3:
                profile.tools_required.append(cleaned)

        # Extract inline "工具：xxx" patterns
        tool_names = re.findall(r"(?:工具[：:]?\s*)([^\n]+)", dep_section)
        for name in tool_names:
            tools = re.split(r"[,，、;；]", name.strip())
            for t in tools:
                t = t.strip().strip("`'\"")
                if len(t) >= 3:
                    profile.tools_required.append(t)


def _extract_capabilities(body: str, profile: SkillProfile, sections: dict[str, str] | None = None):
    """Extract capabilities and features from the skill content."""
    cap_section = _get_section_text(body, ["功能", "能力", "Features", "Capabilities", "支持场景"], sections)

    if cap_section:
        list_items = re.findall(r"[-•]\s*(.+)", cap_section)
        for item in list_items:
            profile.capabilities.append(item.strip())

    # Also look for capability patterns inline
    cap_patterns = [
        r"(?:支持(?:以下)?(?:分析场景|功能|操作)[：:]?\s*)(.*?)(?:\n\n|\n#{1,3}|\Z)",
    ]
    for pattern in cap_patterns:
        matches = re.findall(pattern, body, re.DOTALL | re.IGNORECASE)
        for match in matches:
            items = re.findall(r"[-•]\s*(.+)", match)
            for item in items:
                profile.capabilities.append(item.strip())

    # If still no capabilities, extract from the "概述" section
    if not profile.capabilities:
        overview = _get_section_text(body, ["概述", "Overview", "简介", "描述"], sections)
        if overview:
            # Extract the first meaningful sentences
            sentences = re.split(r"[。\n]", overview)
            for s in sentences:
                s = s.strip()
                if len(s) >= 10 and not s.startswith("#"):
                    profile.capabilities.append(s[:100])
                    if len(profile.capabilities) >= 3:
                        break

    _deduplicate(profile.capabilities, min_len=3)


def _get_section_text(body: str, section_names: list[str], sections: dict[str, str] | None = None) -> str:
    """Get the text content of a section by trying multiple possible section names.

    Args:
        body: Full body text (used only if sections is None).
        section_names: Candidate section header names to search for.
        sections: Pre-built sections map. If None, will be built from body on each call.
    """
    if sections is None:
        sections = {}
        parts = re.split(r"^(#{1,4}\s+.+)$", body, flags=re.MULTILINE)
        for i in range(1, len(parts), 2):
            header = re.sub(r"^#+\s*", "", parts[i].strip())
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            sections[header] = content

    for name in section_names:
        for key, val in sections.items():
            if name.lower() in key.lower():
                return val
    return ""


def _deduplicate(lst: list, min_len: int = 2):
    """Remove duplicates, short entries, and markdown formatting while preserving order."""
    seen = set()
    unique = []
    for item in lst:
        # Strip common markdown formatting but preserve underscores (needed for tool names)
        cleaned = re.sub(r"[*`\[\]#>\-]", "", item).strip()
        normalized = cleaned.lower()
        if normalized not in seen and len(cleaned) >= min_len:
            seen.add(normalized)
            unique.append(cleaned)
    lst[:] = unique
