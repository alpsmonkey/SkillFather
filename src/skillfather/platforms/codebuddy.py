"""CodeBuddy platform adapter.

Skill Format: SKILL.md with YAML frontmatter (same as WorkBuddy)
Storage: ~/.codebuddy/skills/<name>/SKILL.md (user-level)
         <workspace>/.codebuddy/skills/<name>/SKILL.md (project-level)
Resources: scripts/, references/, assets/

Note: CodeBuddy and WorkBuddy share the same SKILL.md format.
The main difference is the storage directory (.codebuddy vs .workbuddy)
and the product branding.
"""

from pathlib import Path
from skillfather.platforms.base import (
    PlatformAdapter, PlatformInfo, register_platform, _parse_yaml_frontmatter
)
from skillfather.parser import SkillProfile


@register_platform("codebuddy")
class CodeBuddyAdapter(PlatformAdapter):

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="codebuddy",
            display_name="CodeBuddy",
            description="CodeBuddy AI 编程助手（WorkBuddy 国际版），使用与 WorkBuddy 相同的 SKILL.md 格式",
            skill_format="SKILL.md (YAML frontmatter + Markdown body)",
            storage_paths=[
                "~/.codebuddy/skills/<name>/SKILL.md",
                "<workspace>/.codebuddy/skills/<name>/SKILL.md",
            ],
            file_extensions=[".md"],
            docs_url="http://www.codebuddy.ai/docs/ide/Features/Skills",
        )

    def detect(self, path: str | Path) -> bool:
        p = Path(path)
        if p.is_file() and p.name == "SKILL.md":
            return ".codebuddy" in str(p.parent)
        if p.is_dir() and (p / "SKILL.md").exists():
            return ".codebuddy" in str(p)
        return False

    def parse(self, path: str | Path) -> SkillProfile:
        # Same format as WorkBuddy, reuse the parser
        from skillfather.parser import parse_skill
        profile = parse_skill(path)
        # Override platform tag
        profile.frontmatter_raw["_platform"] = "codebuddy"
        return profile

    def get_platform_context(self, profile: SkillProfile) -> str:
        info = self.info()
        ctx = super().get_platform_context(profile)

        features = [
            "- YAML frontmatter: name (必需), description (必需)",
            "- 可选字段: allowed-tools, disable-model-invocation, license",
            "- 资源目录: scripts/, references/, assets/",
            "- Progressive Disclosure 三级加载: 元数据 → 正文 → 资源",
        ]
        ctx += f"\nCodeBuddy 特性:\n" + "\n".join(features)
        return ctx
