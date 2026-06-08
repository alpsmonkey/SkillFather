"""Codex / OpenAI Agent platform adapter.

Skill Format: SKILL.md (YAML frontmatter: name, description) + optional agents/openai.yaml
Storage: $CWD/.agents/skills/<name>/SKILL.md (repo-level)
         $HOME/.agents/skills/<name>/SKILL.md (user-level)
         /etc/codex/skills/<name>/SKILL.md (admin-level)
Resources: scripts/, references/, assets/, agents/openai.yaml

Key differences from WorkBuddy:
- Storage path uses .agents/skills/ instead of .workbuddy/skills/
- Optional agents/openai.yaml for UI metadata, policy, and dependencies
- Skills triggered via $skill-name syntax (not /skill-name)
- Supports allow_implicit_invocation policy
"""

import json
from pathlib import Path
from skillfit.platforms.base import (
    PlatformAdapter, PlatformInfo, register_platform, _parse_yaml_frontmatter
)
from skillfit.parser import SkillProfile


@register_platform("codex")
class CodexAdapter(PlatformAdapter):

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="codex",
            display_name="OpenAI Codex Agent",
            description="OpenAI Codex CLI/IDE 智能体技能系统，SKILL.md + agents/openai.yaml 配置",
            skill_format="SKILL.md + agents/openai.yaml",
            storage_paths=[
                "$CWD/.agents/skills/<name>/SKILL.md",
                "$HOME/.agents/skills/<name>/SKILL.md",
                "/etc/codex/skills/<name>/SKILL.md",
            ],
            file_extensions=[".md", ".yaml", ".yml"],
            docs_url="https://developers.openai.ac.cn/codex/skills",
        )

    def detect(self, path: str | Path) -> bool:
        p = Path(path)
        if p.is_file() and p.name == "SKILL.md":
            # Check parent directory
            if ".agents" in str(p.parent) and "skills" in str(p.parent):
                return True
            # Check for agents/openai.yaml in same directory
            if (p.parent / "agents" / "openai.yaml").exists():
                return True
        if p.is_dir() and (p / "SKILL.md").exists():
            return (p / "agents").is_dir()
        return False

    def parse(self, path: str | Path) -> SkillProfile:
        p = Path(path)

        # Resolve to SKILL.md if directory given
        if p.is_dir():
            skill_md = p / "SKILL.md"
            if not skill_md.exists():
                raise FileNotFoundError(f"SKILL.md not found in directory: {p}")
            p = skill_md

        if not p.exists():
            raise FileNotFoundError(f"Skill file not found: {p}")

        content = p.read_text(encoding="utf-8")
        fm, body = _parse_yaml_frontmatter(content)

        profile = SkillProfile(path=str(p.resolve()), raw_content=content)

        # Codex uses name and description as frontmatter
        profile.name = fm.get("title", "") or fm.get("name", "")
        raw_summary = fm.get("summary", "") or fm.get("description", "")
        import re
        profile.summary = re.sub(r"\s*\n\s*", " ", raw_summary).strip()
        profile.frontmatter_raw = fm

        # Parse agents/openai.yaml if it exists
        agents_yaml = p.parent / "agents" / "openai.yaml"
        if agents_yaml.exists():
            self._parse_agents_yaml(agents_yaml, profile)

        # Parse body content using shared utilities
        from skillfit.parser import _parse_content
        _parse_content(content, profile)

        if not profile.name:
            heading_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            if heading_match:
                profile.name = heading_match.group(1).strip()

        return profile

    def _parse_agents_yaml(self, yaml_path: Path, profile: SkillProfile):
        """Parse agents/openai.yaml for additional metadata."""
        try:
            content = yaml_path.read_text(encoding="utf-8")
            # Simple YAML parsing for key fields
            import re

            # Extract display_name
            dn_match = re.search(r"display_name:\s*[\"'](.+?)[\"']", content)
            if dn_match:
                profile.frontmatter_raw["display_name"] = dn_match.group(1)

            # Extract policy
            policy_match = re.search(r"allow_implicit_invocation:\s*(\w+)", content)
            if policy_match:
                profile.frontmatter_raw["allow_implicit_invocation"] = policy_match.group(1)

            # Extract MCP tool dependencies
            tool_matches = re.findall(r"type:\s*[\"']mcp[\"']\s*\n\s*value:\s*[\"'](.+?)[\"']", content)
            for tool in tool_matches:
                profile.tools_required.append(f"mcp:{tool}")

            # Extract default_prompt
            dp_match = re.search(r"default_prompt:\s*[\"'](.+?)[\"']", content, re.DOTALL)
            if dp_match:
                profile.frontmatter_raw["default_prompt"] = dp_match.group(1).strip()

        except Exception:
            pass

    def get_platform_context(self, profile: SkillProfile) -> str:
        info = self.info()
        ctx = super().get_platform_context(profile)

        features = [
            "- 触发方式: $skill-name 语法（非 /slash-command）",
            "- 可选 agents/openai.yaml: UI 元数据 + 策略 + MCP 依赖",
            "- allow_implicit_invocation: false 则仅允许显式调用",
            "- 初始技能列表配额: 上下文窗口的 ~2%",
            "- 支持软链接技能目录",
        ]
        ctx += f"\nCodex 特性:\n" + "\n".join(features)
        return ctx
