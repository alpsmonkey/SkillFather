"""Coze (扣子) platform adapter.

Coze is a visual AI Bot development platform by ByteDance.
Skill Format: Visual (web UI) - exported as .skill or .zip files
              Also supports JSON configuration for programmatic creation.

Since Coze skills are primarily configured through a web UI, analysis
is based on:
1. Exported .skill/.zip files (JSON manifest + code + templates)
2. Skill JSON definitions (if available as files)
3. Documentation/description text (if the user provides a text description)

Key differences from code-first platforms:
- Skills are primarily created via web UI, not files
- Supports workflow nodes (LLM, code, condition, plugin, knowledge base)
- Trigger conditions configured visually (keyword matching modes)
- Input/output parameters defined via structured tables
- Output uses {{variable}} template syntax
"""

import json
import re
import zipfile
from pathlib import Path
from skillfather.platforms.base import (
    PlatformAdapter, PlatformInfo
)
from skillfather.parser import SkillProfile


class CozeAdapter(PlatformAdapter):

    def info(self) -> PlatformInfo:
        return PlatformInfo(
            name="coze",
            display_name="Coze (扣子)",
            description="字节跳动 Coze/扣子平台技能系统，以可视化 Web UI 为主，支持导出 .skill/.zip 文件",
            skill_format="Visual (Web UI) + .skill/.zip 导出 + JSON 定义",
            storage_paths=[
                "Coze Web Platform (https://www.coze.com)",
                "导出的 .skill / .zip 文件",
            ],
            file_extensions=[".skill", ".zip", ".json"],
            docs_url="https://docs.coze.com/",
        )

    def detect(self, path: str | Path) -> bool:
        p = Path(path)
        if p.suffix in (".skill", ".zip"):
            return True
        if p.suffix == ".json":
            try:
                content = p.read_text(encoding="utf-8", errors="ignore")
                data = json.loads(content)
                # Heuristic: Coze JSON definitions often have specific fields
                return any(k in data for k in ("workflow", "plugin_list", "skill_type"))
            except (json.JSONDecodeError, Exception):
                pass
        return False

    def parse(self, path: str | Path) -> SkillProfile:
        p = Path(path)

        if p.suffix == ".zip":
            return self._parse_zip(p)
        elif p.suffix == ".skill":
            return self._parse_skill_file(p)
        elif p.suffix == ".json":
            return self._parse_json(p)
        elif p.is_file():
            # Fallback: treat as text description
            return self._parse_text(p)
        else:
            raise FileNotFoundError(f"Cannot parse Coze skill from: {p}")

    def _parse_zip(self, path: Path) -> SkillProfile:
        """Parse a .zip exported Coze skill."""
        try:
            with zipfile.ZipFile(path, "r") as zf:
                # Validate archive integrity before extracting
                bad_file = zf.testzip()
                if bad_file is not None:
                    print(f"[WARN] Coze ZIP integrity check failed on: {bad_file}")

                # Look for manifest or config files
                names = zf.namelist()
                manifest_path = None
                for candidate in ("manifest.json", "skill.json", "config.json", "index.json"):
                    if candidate in names:
                        manifest_path = candidate
                        break

                if manifest_path:
                    content = zf.read(manifest_path).decode("utf-8")
                    profile = self._parse_json_content(json.loads(content), str(path))
                else:
                    # Fallback: read all text files
                    all_text = []
                    for name in names:
                        if name.endswith((".md", ".txt", ".json")):
                            try:
                                all_text.append(zf.read(name).decode("utf-8"))
                            except Exception:
                                pass
                    profile = SkillProfile(
                        path=str(path.resolve()),
                        raw_content="\n".join(all_text),
                    )
                    profile.name = path.stem
                    profile.summary = "Coze 技能 (从 .zip 导出)"
                    profile.description = "\n".join(all_text)[:500]
                    profile.instructions = "\n".join(all_text)

                # Extract code files for dependency analysis
                for name in names:
                    if name.endswith((".py", ".js", ".ts")):
                        try:
                            code = zf.read(name).decode("utf-8")
                            self._extract_deps_from_code(code, profile)
                        except Exception:
                            pass

                return profile

        except zipfile.BadZipFile:
            # Try as plain text
            return self._parse_text(path)

    def _parse_skill_file(self, path: Path) -> SkillProfile:
        """Parse a .skill file (may be JSON or binary)."""
        try:
            content = path.read_text(encoding="utf-8")
            try:
                data = json.loads(content)
                return self._parse_json_content(data, str(path))
            except json.JSONDecodeError:
                return self._parse_text(path)
        except UnicodeDecodeError:
            # Binary format - provide basic info
            return SkillProfile(
                path=str(path.resolve()),
                raw_content=f"[Binary .skill file: {path.name}]",
                name=path.stem,
                summary=f"Coze 技能 (二进制格式: {path.stat().st_size} bytes)",
            )

    def _parse_json(self, path: Path) -> SkillProfile:
        """Parse a JSON skill definition."""
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
        return self._parse_json_content(data, str(path))

    def _parse_json_content(self, data: dict, source_path: str) -> SkillProfile:
        """Extract SkillProfile from a Coze JSON definition."""
        profile = SkillProfile(
            path=source_path,
            raw_content=json.dumps(data, ensure_ascii=False, indent=2),
        )

        # Common fields in Coze JSON
        profile.name = data.get("name", "") or data.get("title", "") or data.get("skill_name", "")
        profile.summary = data.get("description", "") or data.get("summary", "")

        # Extract trigger keywords
        triggers_raw = data.get("trigger_words", []) or data.get("keywords", []) or []
        if isinstance(triggers_raw, list):
            profile.triggers = [str(t) for t in triggers_raw if len(str(t)) >= 2]

        # Extract input parameters as requirements
        inputs = data.get("input_parameters", []) or data.get("parameters", {}) or {}
        if isinstance(inputs, dict):
            props = inputs.get("properties", {})
            for prop_name, prop_def in props.items():
                if isinstance(prop_def, dict):
                    desc = prop_def.get("description", prop_name)
                    profile.requirements.append(f"输入参数: {prop_name} - {desc}")
        elif isinstance(inputs, list):
            for inp in inputs:
                if isinstance(inp, dict):
                    name = inp.get("name", inp.get("parameter_name", ""))
                    desc = inp.get("prompt", inp.get("description", ""))
                    profile.requirements.append(f"输入参数: {name} - {desc}")

        # Extract capabilities from workflow nodes
        workflow = data.get("workflow", data.get("nodes", []))
        if isinstance(workflow, list):
            for node in workflow:
                if isinstance(node, dict):
                    node_type = node.get("type", node.get("node_type", ""))
                    node_desc = node.get("title", node.get("name", node_type))
                    if node_type:
                        profile.capabilities.append(f"工作流节点: {node_type} ({node_desc})")

        # Extract tool dependencies
        plugins = data.get("plugins", []) or data.get("plugin_list", [])
        if isinstance(plugins, list):
            for plugin in plugins:
                if isinstance(plugin, dict):
                    plugin_name = plugin.get("name", plugin.get("plugin_name", ""))
                    if plugin_name:
                        profile.tools_required.append(f"coze-plugin:{plugin_name}")
                elif isinstance(plugin, str):
                    profile.tools_required.append(f"coze-plugin:{plugin}")

        profile.frontmatter_raw = data
        profile.instructions = json.dumps(data, ensure_ascii=False, indent=2)

        return profile

    def _parse_text(self, path: Path) -> SkillProfile:
        """Parse a text description of a Coze skill."""
        content = path.read_text(encoding="utf-8", errors="ignore")
        profile = SkillProfile(path=str(path.resolve()), raw_content=content)

        # Try YAML frontmatter
        fm, body = self._parse_simple_frontmatter(content)
        if fm:
            profile.frontmatter_raw = fm
            profile.name = fm.get("name", "") or fm.get("title", "")
            profile.summary = fm.get("description", "") or fm.get("summary", "")

        if not profile.name:
            profile.name = path.stem

        profile.instructions = body or content
        profile.description = body[:200] if body else content[:200]

        # Extract keywords
        keywords = re.findall(r"触发词[：:]\s*(.+)", content)
        for kw in keywords:
            items = re.split(r"[,，、;；]", kw.strip())
            profile.triggers.extend(item.strip() for item in items if len(item.strip()) >= 2)

        return profile

    def _parse_simple_frontmatter(self, content: str) -> tuple[dict, str]:
        """Minimal frontmatter parser for non-YAML text."""
        import re
        pattern = r"^---\s*\n(.*?)\n---\s*\n"
        match = re.match(pattern, content, re.DOTALL)
        if not match:
            return {}, content
        yaml_str = match.group(1)
        body = content[match.end():]
        fm: dict = {}
        for line in yaml_str.split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                key = key.strip()
                value = value.strip().strip("\"'")
                if value:
                    fm[key] = value
        return fm, body

    def _extract_deps_from_code(self, code: str, profile: SkillProfile):
        """Extract dependencies from Python/JS code in Coze skill."""
        # Python imports
        py_imports = re.findall(r"^(?:import|from)\s+(\S+)", code, re.MULTILINE)
        for imp in py_imports:
            pkg = imp.split(".")[0]
            if pkg not in ("os", "sys", "json", "re", "time", "datetime", "pathlib"):
                profile.dependencies.append(pkg)

        # JS/TS requires
        js_requires = re.findall(r"(?:require|import)\s*\(?[\"']([^\"']+)", code)
        for req in js_requires:
            pkg = req.split("/")[0]
            if not pkg.startswith("."):
                profile.dependencies.append(pkg)

    def get_platform_context(self, profile: SkillProfile) -> str:
        info = self.info()
        ctx = super().get_platform_context(profile)

        features = [
            "- 主要通过 Web UI 可视化配置（非文件驱动）",
            "- 支持工作流节点: LLM, 代码, 条件分支, 循环, 插件, 知识库",
            "- 触发词匹配模式: 包含任意 / 包含全部 / 完全匹配",
            "- 输出模板语法: {{变量名}}",
            "- 支持 .skill/.zip 导出导入",
            "- 知识库 RAG 集成",
        ]
        ctx += f"\nCoze 特性:\n" + "\n".join(features)
        return ctx
