"""Unit tests for the SKILL.md parser."""

import pytest
from pathlib import Path
from skillfather.parser import parse_skill, SkillProfile

EXAMPLES_DIR = Path(__file__).parent.parent / "examples"
SAMPLE_SKILL = EXAMPLES_DIR / "sample_skill.md"


class TestParseSkill:
    """Test parse_skill function."""

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            parse_skill("/nonexistent/SKILL.md")

    def test_parse_sample(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert isinstance(profile, SkillProfile)
        assert profile.path == str(SAMPLE_SKILL.resolve())

    def test_frontmatter_extraction(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert "SAP 成本分析" in profile.name
        assert "IMA 知识库" in profile.summary

    def test_read_when(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert len(profile.read_when) >= 1

    def test_triggers(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert len(profile.triggers) >= 3
        assert any("CKM3" in t for t in profile.triggers)
        assert any("物料账" in t for t in profile.triggers)

    def test_tools_required(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert len(profile.tools_required) >= 2

    def test_capabilities(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert len(profile.capabilities) >= 2

    def test_requirements(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert len(profile.requirements) >= 1

    def test_all_sections(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert len(profile.all_sections) >= 3

    def test_instructions_not_empty(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert len(profile.instructions) > 100

    def test_display_name(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert "SAP" in profile.display_name

    def test_trigger_text(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert len(profile.trigger_text) > 10

    def test_tool_text(self):
        profile = parse_skill(SAMPLE_SKILL)
        assert len(profile.tool_text) > 10


class TestSkillProfile:
    """Test SkillProfile data class properties."""

    def test_empty_profile_defaults(self):
        profile = SkillProfile(path="/test/SKILL.md", raw_content="# Test\n")
        assert profile.display_name == "SKILL"
        assert profile.trigger_text == "未检测到触发词"
        assert profile.requirement_text == "未检测到前置条件"
        assert profile.tool_text == "未检测到工具依赖"
        assert profile.capability_text == "未检测到功能描述"
