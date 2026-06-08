"""Hermes Agent platform adapter.

Skill Format: SKILL.md with rich YAML frontmatter (name, description, version, author,
             license, platforms, metadata.hermes.*, required_environment_variables,
             required_credential_files)
Storage: ~/.hermes/skills/<category>/<name>/SKILL.md (primary)
         ~/.hermes/optional-skills/<category>/<name>/SKILL.md (optional)
         External dirs via config.yaml skills.external_dirs
Resources: scripts/, references/, templates/, assets/

Key differences from WorkBuddy:
- Requires version, author, license fields
- Has metadata.hermes block with tags, category, conditional activation
- Supports platform restrictions (macos, linux, windows)
- Supports conditional activation (requires_toolsets, requires_tools, fallback_for_*)
- Supports required_environment_variables (auto-injected to sandbox)
- Supports required_credential_files (auto-mounted to containers)
- Template variables: ${HERMES_SKILL_DIR}, ${HERMES_SESSION_ID}
- Inline shell: !`cmd`
- Skills managed via skill_manage tool (create, patch, edit, delete)
"""

import re
from pathlib import Path
from skillfit.platforms.base import (
    PlatformAdapter, PlatformInfo, register_platform, _parse_yaml_frontmatter
)
from skillfit.parser import SkillProfile


@register_platform("hermes")
class HermesAdapter(PlatformAdapter):

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="hermes",
            display_name="Hermes Agent (Nous Research)",
            description="Hermes Agent 开源智能体框架技能系统，SKILL.md + 丰富的 YAML 元数据",
            skill_format="SKILL.md (丰富 YAML frontmatter + Markdown body)",
            storage_paths=[
                "~/.hermes/skills/<category>/<name>/SKILL.md",
                "~/.hermes/optional-skills/<category>/<name>/SKILL.md",
                "外部目录 (config.yaml skills.external_dirs)",
            ],
            file_extensions=[".md"],
            docs_url="https://hermes-agent.nousresearch.com/docs/developer-guide/creating-skills/",
        )

    def detect(self, path: str | Path) -> bool:
        p = Path(path)
        if p.is_file() and p.name == "SKILL.md":
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                return "metadata:" in content and "hermes:" in content
            except Exception:
                return False
        if p.is_dir() and (p / "SKILL.md").exists():
            try:
                content = (p / "SKILL.md").read_text(encoding="utf-8", errors="ignore")
                return "metadata:" in content and "hermes:" in content
            except Exception:
                return False
        return False

    def parse(self, path: str | Path) -> SkillProfile:
        p = Path(path)

        # Resolve to SKILL.md
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

        # Hermes-specific frontmatter mapping
        profile.name = fm.get("title", "") or fm.get("name", "")
        raw_summary = fm.get("summary", "") or fm.get("description", "")
        profile.summary = re.sub(r"\s*\n\s*", " ", raw_summary).strip()
        profile.frontmatter_raw = fm

        # Extract Hermes-specific fields
        self._extract_hermes_metadata(fm, profile)

        # Parse body content using shared parser
        from skillfit.parser import _parse_content
        _parse_content(content, profile)

        if not profile.name:
            heading_match = re.search(r"^#\s+(.+)", content, re.MULTILINE)
            if heading_match:
                profile.name = heading_match.group(1).strip()

        return profile

    def _extract_hermes_metadata(self, fm: dict, profile: SkillProfile):
        """Extract Hermes-specific metadata fields."""
        # Version, author, license
        for key in ("version", "author", "license"):
            val = fm.get(key, "")
            if val:
                profile.frontmatter_raw[f"_hermes_{key}"] = val

        # Platform restrictions
        platforms = fm.get("platforms", "")
        if isinstance(platforms, list):
            profile.frontmatter_raw["_hermes_platforms"] = platforms
            profile.requirements.append(f"平台限制: {', '.join(platforms)}")

        # Metadata.hermes tags and category
        metadata = fm.get("metadata", {})
        if isinstance(metadata, dict):
            hermes_meta = metadata.get("hermes", {})
            if isinstance(hermes_meta, dict):
                # Tags
                tags = hermes_meta.get("tags", [])
                if isinstance(tags, list):
                    profile.frontmatter_raw["_hermes_tags"] = tags
                    profile.triggers.extend(str(t) for t in tags if len(str(t)) >= 2)

                # Category
                category = hermes_meta.get("category", "")
                if category:
                    profile.frontmatter_raw["_hermes_category"] = category

                # Conditional activation
                for cond_key in ("requires_toolsets", "requires_tools", "fallback_for_toolsets", "fallback_for_tools"):
                    vals = hermes_meta.get(cond_key, [])
                    if isinstance(vals, list) and vals:
                        profile.frontmatter_raw[f"_hermes_{cond_key}"] = vals
                        profile.requirements.append(f"{cond_key}: {', '.join(str(v) for v in vals)}")

                # Config requirements
                config_items = hermes_meta.get("config", [])
                if isinstance(config_items, list):
                    for cfg in config_items:
                        if isinstance(cfg, dict):
                            key_name = cfg.get("key", "")
                            desc = cfg.get("description", "")
                            profile.requirements.append(f"配置项: {key_name} - {desc}")

        # Required environment variables
        env_vars = fm.get("required_environment_variables", [])
        if isinstance(env_vars, list):
            for env in env_vars:
                if isinstance(env, dict):
                    env_name = env.get("name", "")
                    prompt = env.get("prompt", "")
                    help_text = env.get("help", "")
                    profile.requirements.append(f"环境变量: {env_name} ({prompt or help_text})")
                    # Mark as env dependency for scoring
                    profile.tools_required.append(f"env:{env_name}")

        # Required credential files
        cred_files = fm.get("required_credential_files", [])
        if isinstance(cred_files, list):
            for cred in cred_files:
                if isinstance(cred, dict):
                    cred_path = cred.get("path", "")
                    desc = cred.get("description", "")
                    profile.requirements.append(f"凭证文件: {cred_path} ({desc})")

        # Related skills
        hermes_meta = fm.get("metadata", {})
        if isinstance(hermes_meta, dict):
            hermes_data = hermes_meta.get("hermes", {})
            if isinstance(hermes_data, dict):
                related = hermes_data.get("related_skills", [])
                if isinstance(related, list):
                    profile.frontmatter_raw["_hermes_related"] = related
                    for rs in related:
                        profile.dependencies.append(f"关联技能: {rs}")

    def get_platform_context(self, profile: SkillProfile) -> str:
        info = self.info()
        ctx = super().get_platform_context(profile)

        features = [
            "- 触发方式: /skill-name 斜杠命令 + 自然语言自动触发",
            "- 条件激活: requires_toolsets, requires_tools, fallback_for_*",
            "- 平台限制: platforms 字段 (macos/linux/windows)",
            "- 环境变量自动注入沙箱 (required_environment_variables)",
            "- 凭证文件自动挂载 (required_credential_files)",
            "- 模板变量: ${HERMES_SKILL_DIR}, ${HERMES_SESSION_ID}",
            "- Agent 自管理: skill_manage (create/patch/edit/delete)",
            "- 渐进式披露: skills_list() → skill_view() → references/",
        ]
        ctx += f"\nHermes 特性:\n" + "\n".join(features)

        # Add Hermes-specific tags/category info
        tags = profile.frontmatter_raw.get("_hermes_tags", [])
        category = profile.frontmatter_raw.get("_hermes_category", "")
        if tags:
            ctx += f"\n标签: {', '.join(str(t) for t in tags)}"
        if category:
            ctx += f"\n分类: {category}"

        return ctx
