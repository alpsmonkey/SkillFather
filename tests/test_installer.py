"""Tests for skillfather.installer module."""

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from skillfather.installer import (
    _find_skill_md,
    install_skill,
    uninstall_skill,
    TARGET_DIR,
    TARGET_FILE,
)


class TestFindSkillMd:
    """Tests for _find_skill_md()."""

    def test_find_skill_md_returns_path(self):
        """_find_skill_md 应该能找到 SKILL.md 文件。"""
        result = _find_skill_md()
        assert result is not None
        assert result.is_file()
        assert result.name == "SKILL.md"

    def test_find_skill_md_content_has_frontmatter(self):
        """找到的 SKILL.md 应包含 YAML frontmatter。"""
        result = _find_skill_md()
        assert result is not None
        content = result.read_text(encoding="utf-8")
        assert content.startswith("---")
        assert "name: SkillFather" in content


class TestInstallSkill:
    """Tests for install_skill()."""

    def test_install_skill_to_temp_dir(self, tmp_path):
        """install_skill 应将 SKILL.md 复制到目标目录。"""
        # 用 patch 把 TARGET_DIR 和 TARGET_FILE 指向临时目录
        temp_target_dir = tmp_path / "skillfather"
        temp_target_file = temp_target_dir / "SKILL.md"

        with patch("skillfather.installer.TARGET_DIR", temp_target_dir), \
             patch("skillfather.installer.TARGET_FILE", temp_target_file):
            result = install_skill(force=True)

        assert result is True
        assert temp_target_file.exists()
        content = temp_target_file.read_text(encoding="utf-8")
        assert "SkillFather" in content

    def test_install_skill_skip_if_exists(self, tmp_path):
        """已存在且未指定 force 时应跳过。"""
        temp_target_dir = tmp_path / "skillfather"
        temp_target_dir.mkdir()
        temp_target_file = temp_target_dir / "SKILL.md"
        temp_target_file.write_text("old content", encoding="utf-8")

        with patch("skillfather.installer.TARGET_DIR", temp_target_dir), \
             patch("skillfather.installer.TARGET_FILE", temp_target_file):
            result = install_skill(force=False)

        assert result is False
        # 内容应未被覆盖
        assert temp_target_file.read_text(encoding="utf-8") == "old content"

    def test_install_skill_force_overwrites(self, tmp_path):
        """force=True 时应覆盖已有文件。"""
        temp_target_dir = tmp_path / "skillfather"
        temp_target_dir.mkdir()
        temp_target_file = temp_target_dir / "SKILL.md"
        temp_target_file.write_text("old content", encoding="utf-8")

        with patch("skillfather.installer.TARGET_DIR", temp_target_dir), \
             patch("skillfather.installer.TARGET_FILE", temp_target_file):
            result = install_skill(force=True)

        assert result is True
        content = temp_target_file.read_text(encoding="utf-8")
        assert "SkillFather" in content
        assert "old content" not in content


class TestUninstallSkill:
    """Tests for uninstall_skill()."""

    def test_uninstall_skill_removes_file(self, tmp_path):
        """uninstall_skill 应删除目标文件。"""
        temp_target_dir = tmp_path / "skillfather"
        temp_target_dir.mkdir()
        temp_target_file = temp_target_dir / "SKILL.md"
        temp_target_file.write_text("content", encoding="utf-8")

        with patch("skillfather.installer.TARGET_DIR", temp_target_dir), \
             patch("skillfather.installer.TARGET_FILE", temp_target_file):
            result = uninstall_skill()

        assert result is True
        assert not temp_target_file.exists()

    def test_uninstall_skill_skip_if_not_exists(self, tmp_path):
        """未安装时应跳过。"""
        temp_target_dir = tmp_path / "skillfather"
        temp_target_file = temp_target_dir / "SKILL.md"

        with patch("skillfather.installer.TARGET_DIR", temp_target_dir), \
             patch("skillfather.installer.TARGET_FILE", temp_target_file):
            result = uninstall_skill()

        assert result is False
