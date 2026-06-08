"""WorkBuddy platform adapter.

Skill Format: SKILL.md with YAML frontmatter
Storage: ~/.workbuddy/skills/<name>/SKILL.md (user-level)
         <workspace>/.workbuddy/skills/<name>/SKILL.md (project-level)
Resources: scripts/, references/, assets/
"""

from pathlib import Path
from skillfather.platforms.base import (
    PlatformAdapter, PlatformInfo, _parse_yaml_frontmatter
)
from skillfather.parser import SkillProfile, _parse_content


class WorkBuddyAdapter(PlatformAdapter):

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="workbuddy",
            display_name="WorkBuddy",
            description="WorkBuddy AI 编程助手的 Skill 系统，支持 YAML frontmatter + Markdown 指令的 SKILL.md 格式",
            skill_format="SKILL.md (YAML frontmatter + Markdown body)",
            storage_paths=[
                "~/.workbuddy/skills/<name>/SKILL.md",
                "<workspace>/.workbuddy/skills/<name>/SKILL.md",
            ],
            file_extensions=[".md"],
            docs_url="http://www.codebuddy.ai/docs/zh/ide/Features/Skills",
        )

    def detect(self, path: str | Path) -> bool:
        p = Path(path)
        if p.is_file() and p.name == "SKILL.md":
            parent_str = str(p.parent)
            return ".workbuddy" in parent_str or "skills" in parent_str.lower()
        if p.is_dir() and (p / "SKILL.md").exists():
            return True
        return False

    def parse(self, path: str | Path) -> SkillProfile:
        from skillfather.parser import parse_skill
        return parse_skill(path)

    def get_platform_context(self, profile: SkillProfile) -> str:
        info = self.info()
        ctx = super().get_platform_context(profile)

        # WorkBuddy-specific context
        features = []
        features.append("- 5 层记忆系统（云记忆 + 本地 MEMORY.md + workspace memory）")
        features.append("- 支持 MCP 工具集成")
        features.append("- 支持 Slash Commands 手动触发")
        features.append("- 支持 Progressive Disclosure 渐进式加载")

        ctx += f"\n平台特性:\n" + "\n".join(features)

        # Check for specific WorkBuddy frontmatter fields
        allowed_tools = profile.frontmatter_raw.get("allowed-tools", "")
        if allowed_tools:
            ctx += f"\n允许工具: {allowed_tools}"

        return ctx
