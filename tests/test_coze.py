"""Unit tests for Coze platform adapter — .zip parsing, .skill parsing, JSON parsing."""

import pytest
import json
import tempfile
import zipfile
import os
from pathlib import Path
from skillfather.platforms.coze import CozeAdapter


def _create_zip(files: dict[str, str], suffix: str = ".zip") -> str:
    """Create a zip file with given {filename: content} entries. Returns path."""
    f = tempfile.NamedTemporaryFile(mode="wb", suffix=suffix, delete=False)
    with zipfile.ZipFile(f, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    f.close()
    return f.name


def _create_json_file(data: dict) -> str:
    """Create a JSON file with given data. Returns path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(data, f, ensure_ascii=False)
    f.close()
    return f.name


def _create_text_file(content: str, suffix: str = ".md") -> str:
    """Create a text file. Returns path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


class TestCozeAdapterInfo:
    """Test CozeAdapter.info()."""

    def test_info_fields(self):
        adapter = CozeAdapter()
        info = adapter.info()
        assert info.name == "coze"
        assert "Coze" in info.display_name or "扣子" in info.display_name
        assert ".zip" in info.file_extensions
        assert ".json" in info.file_extensions


class TestCozeDetect:
    """Test CozeAdapter.detect()."""

    def test_detect_zip(self):
        path = _create_zip({"test.txt": "hello"})
        try:
            assert CozeAdapter().detect(path) is True
        finally:
            os.unlink(path)

    def test_detect_json_with_workflow(self):
        path = _create_json_file({"workflow": [], "name": "test"})
        try:
            assert CozeAdapter().detect(path) is True
        finally:
            os.unlink(path)

    def test_detect_json_without_coze_fields(self):
        path = _create_json_file({"foo": "bar"})
        try:
            # No Coze-specific keys, should not detect
            assert CozeAdapter().detect(path) is False
        finally:
            os.unlink(path)

    def test_detect_skill_extension(self):
        path = _create_text_file("{}", suffix=".skill")
        try:
            assert CozeAdapter().detect(path) is True
        finally:
            os.unlink(path)


class TestCozeParseZip:
    """Test CozeAdapter._parse_zip via parse()."""

    def test_zip_with_manifest(self):
        """Zip with manifest.json should extract structured profile."""
        manifest = {
            "name": "Test Coze Skill",
            "description": "A test Coze skill",
            "trigger_words": ["你好", "hello"],
            "workflow": [
                {"type": "llm", "title": "ChatGPT Node"},
            ],
        }
        path = _create_zip({
            "manifest.json": json.dumps(manifest, ensure_ascii=False),
            "main.py": "import requests\nfrom openai import OpenAI\n",
        })
        try:
            profile = CozeAdapter().parse(path)
            assert "Test Coze Skill" in profile.name
            assert len(profile.triggers) >= 1
            assert len(profile.capabilities) >= 1  # workflow node extracted
        finally:
            os.unlink(path)

    def test_zip_without_manifest(self):
        """Zip without manifest should fallback to text extraction."""
        path = _create_zip({
            "readme.md": "# My Skill\n\nThis is a Coze skill description.",
            "config.json": '{"version": "1.0"}',
        })
        try:
            profile = CozeAdapter().parse(path)
            # Should still produce a profile (fallback)
            assert profile.raw_content != ""
            assert "Coze" in profile.summary or len(profile.raw_content) > 0
        finally:
            os.unlink(path)

    def test_zip_with_code_dependencies(self):
        """Zip with .py files should extract import dependencies."""
        code = "import requests\nimport numpy as np\nfrom openai import OpenAI\n"
        path = _create_zip({
            "manifest.json": json.dumps({"name": "Code Dep Test"}, ensure_ascii=False),
            "handler.py": code,
        })
        try:
            profile = CozeAdapter().parse(path)
            # requests, openai should be detected as dependencies
            dep_names = [d.lower() for d in profile.dependencies]
            assert "requests" in dep_names
        finally:
            os.unlink(path)


class TestCozeParseJson:
    """Test CozeAdapter._parse_json via parse()."""

    def test_json_with_all_fields(self):
        data = {
            "name": "Full Feature Skill",
            "description": "A complete test skill",
            "trigger_words": ["触发1", "触发2"],
            "input_parameters": [
                {"name": "input1", "description": "First input"},
            ],
            "workflow": [
                {"type": "llm", "title": "LLM Node"},
                {"type": "code", "title": "Code Node"},
            ],
            "plugins": [
                {"name": "search_plugin"},
                "weather_plugin",
            ],
        }
        path = _create_json_file(data)
        try:
            profile = CozeAdapter().parse(path)
            assert "Full Feature" in profile.name
            assert len(profile.triggers) >= 1
            assert len(profile.capabilities) >= 1
        finally:
            os.unlink(path)


class TestCozeParseSkillFile:
    """Test CozeAdapter._parse_skill_file via parse()."""

    def test_skill_json_format(self):
        """A .skill file containing JSON should be parsed as JSON."""
        data = {"name": "Skill File Test", "description": "From .skill file"}
        content = json.dumps(data, ensure_ascii=False)
        path = _create_text_file(content, suffix=".skill")
        try:
            profile = CozeAdapter().parse(path)
            assert "Skill File Test" in profile.name
        finally:
            os.unlink(path)
