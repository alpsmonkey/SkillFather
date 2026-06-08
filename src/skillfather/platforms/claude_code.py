"""Claude Code platform adapter.

Skill Format: .claude/commands/*.md (Markdown with optional YAML frontmatter)
              .claude/skills/*/SKILL.md (Claude Code 1.0+ Skills)
Storage: .claude/commands/<name>.md (project-level)
         ~/.claude/commands/<name>.md (user-level)
         .claude/skills/<name>/SKILL.md (project-level)
         ~/.claude/skills/<name>/SKILL.md (user-level)

Key differences from WorkBuddy:
- Commands are simple Markdown files (not necessarily SKILL.md)
- Support $ARGUMENTS, $1, $2 parameter placeholders
- Triggered via /command-name syntax
- Optional YAML frontmatter with description and allowed_tools
- Skills and Commands are now unified (commands/*.md == skills/*/SKILL.md)
"""

import re
from pathlib import Path
from skillfather.platforms.base import (
    PlatformAdapter, PlatformInfo, register_platform, _parse_yaml_frontmatter
)
from skillfather.parser import SkillProfile


@register_platform("claude-code")
class ClaudeCodeAdapter(PlatformAdapter):

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="claude-code",
            display_name="Claude Code (Anthropic)",
            description="Anthropic Claude Code 的自定义命令/技能系统，使用 .claude/commands/*.md Markdown 格式",
            skill_format=".claude/commands/*.md 或 .claude/skills/*/SKILL.md",
            storage_paths=[
                ".claude/commands/<name>.md (project)",
                "~/.claude/commands/<name>.md (user)",
                ".claude/skills/<name>/SKILL.md (project)",
                "~/.claude/skills/<name>/SKILL.md (user)",
            ],
            file_extensions=[".md"],
            docs_url="https://code.claude.com/docs/en/agent-sdk/slash-commands",
        )

    def detect(self, path: str | Path) -> bool:
        p = Path(path)
        parts = str(p)
        # .claude/commands/*.md
        if ".claude" in parts and "commands" in parts and p.suffix == ".md":
            return True
        # .claude/skills/*/SKILL.md
        if ".claude" in parts and "skills" in parts and p.name == "SKILL.md":
            return True
        return False

    def parse(self, path: str | Path) -> SkillProfile:
        p = Path(path)

        # Resolve to actual .md file
        if p.is_dir():
            # Could be .claude/commands/ directory
            if p.name == "commands" or p.name == "skills":
                raise ValueError(
                    f"Please specify a specific .md file, not the directory: {p}. "
                    f"Example: {p}/review.md"
                )
            # Could be a skill directory
            skill_md = p / "SKILL.md"
            if skill_md.exists():
                p = skill_md
            else:
                raise FileNotFoundError(f"SKILL.md not found in directory: {p}")

        if not p.exists():
            raise FileNotFoundError(f"Command file not found: {p}")

        content = p.read_text(encoding="utf-8")
        fm, body = _parse_yaml_frontmatter(content)

        profile = SkillProfile(path=str(p.resolve()), raw_content=content)

        # Claude Code uses description in frontmatter; name comes from filename
        command_name = p.stem  # e.g., "review" from "review.md"
        profile.name = command_name
        profile.frontmatter_raw["command_name"] = command_name

        # Description from frontmatter
        raw_desc = fm.get("description", "")
        profile.summary = re.sub(r"\s*\n\s*", " ", raw_desc).strip() if raw_desc else ""
        profile.frontmatter_raw = fm

        # Allowed tools
        allowed_tools = fm.get("allowed_tools", "")
        if isinstance(allowed_tools, str) and allowed_tools:
            # Parse like ["Bash(git*)", "Bash(npm*)"]
            tools = re.findall(r"[\"]?(\w+[\w()-*]*)[\"]?", allowed_tools)
            profile.tools_required = [t for t in tools if len(t) >= 2]
        elif isinstance(allowed_tools, list):
            profile.tools_required = [str(t) for t in allowed_tools]

        # Parse body content
        self._parse_command_body(body, profile)

        return profile

    def _parse_command_body(self, body: str, profile: SkillProfile):
        """Extract information from Claude Code command body."""
        # Check for parameter placeholders
        if "$ARGUMENTS" in body or "$1" in body or "$2" in body:
            profile.frontmatter_raw["has_arguments"] = True
            params = []
            if "$ARGUMENTS" in body:
                params.append("$ARGUMENTS (全部参数)")
            for i in range(1, 6):
                if f"${i}" in body:
                    params.append(f"${i} (第{i}个参数)")
            profile.requirements = params

        # Parse sections (same as SKILL.md)
        sections = re.split(r"^(#{1,4}\s+.+)$", body, flags=re.MULTILINE)
        for i in range(1, len(sections), 2):
            header = re.sub(r"^#+\s*", "", sections[i].strip())
            content_text = sections[i + 1].strip() if i + 1 < len(sections) else ""
            profile.all_sections[header] = content_text

        # Extract triggers from "何时使用" / "When to use" sections
        trigger_section = self._get_section(body, ["何时使用", "When to Use", "使用场景", "适用场景"])
        if trigger_section:
            items = re.findall(r"[-•]\s*(.+)", trigger_section)
            profile.triggers = [item.strip() for item in items if len(item.strip()) >= 2]

        # Extract capabilities from sections
        cap_section = self._get_section(body, ["功能", "能力", "Features", "分析维度", "检查项"])
        if cap_section:
            items = re.findall(r"[-•]\s*(.+)", cap_section)
            profile.capabilities = [item.strip() for item in items if len(item.strip()) >= 2]

        # Description: first meaningful paragraph
        if not profile.description:
            paragraphs = re.split(r"\n\n+", body)
            for para in paragraphs:
                clean = re.sub(r"[#*\-`>\[\]()$]", "", para).strip()
                if len(clean) >= 20:
                    profile.description = clean[:200]
                    break

        profile.instructions = body

    def _get_section(self, body: str, names: list[str]) -> str:
        """Get section text by trying multiple names."""
        sections = {}
        parts = re.split(r"^(#{1,4}\s+.+)$", body, flags=re.MULTILINE)
        for i in range(1, len(parts), 2):
            header = re.sub(r"^#+\s*", "", parts[i].strip())
            content = parts[i + 1].strip() if i + 1 < len(parts) else ""
            sections[header] = content
        for name in names:
            for key, val in sections.items():
                if name.lower() in key.lower():
                    return val
        return ""

    def get_platform_context(self, profile: SkillProfile) -> str:
        info = self.info()
        ctx = super().get_platform_context(profile)

        features = [
            "- 触发方式: /command-name 语法",
            "- 参数变量: $ARGUMENTS, $1, $2, ...",
            "- 可选 frontmatter: description (必需), allowed_tools (可选)",
            "- MCP 命令格式: /mcp__<server>__<command>",
            "- Commands 和 Skills 已统一（同一路径映射）",
        ]
        ctx += f"\nClaude Code 特性:\n" + "\n".join(features)

        has_args = profile.frontmatter_raw.get("has_arguments", False)
        if has_args:
            ctx += "\n命令支持参数输入"
        return ctx
