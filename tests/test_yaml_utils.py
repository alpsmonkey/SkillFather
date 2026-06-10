"""Unit tests for yaml_utils — standalone YAML frontmatter parser."""

import pytest
from skillfather.yaml_utils import parse_yaml_frontmatter


class TestParseYAMLFrontmatter:
    """Test parse_yaml_frontmatter with various input formats."""

    def test_no_frontmatter(self):
        """Content without frontmatter returns empty dict and original content."""
        content = "# Hello\n\nSome text."
        fm, body = parse_yaml_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_empty_frontmatter(self):
        """Empty frontmatter (---\n---) returns empty dict."""
        content = "---\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        assert fm == {}
        assert "# Hello" in body

    def test_simple_key_value(self):
        """Simple key: value pairs."""
        content = "---\nname: Test Skill\nversion: 1.0\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        assert fm.get("name") == "Test Skill"
        assert fm.get("version") == "1.0"
        assert "# Hello" in body

    def test_inline_list(self):
        """Inline list [a, b, c]."""
        content = "---\nplatforms: [macos, linux, windows]\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        assert fm["platforms"] == ["macos", "linux", "windows"]

    def test_indented_list_items(self):
        """YAML list with - item syntax."""
        content = "---\nread_when:\n  - 每次会话开始\n  - 需要确认边界\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        assert "read_when" in fm
        assert isinstance(fm["read_when"], (list, dict))

    def test_nested_dict(self):
        """Nested YAML key: sub-key: value."""
        content = "---\nmetadata:\n  hermes:\n    tags: [a, b]\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        assert "metadata" in fm
        assert isinstance(fm["metadata"], dict)

    def test_folded_scalar_greater_than(self):
        """YAML folded scalar (>) joins lines with spaces."""
        content = "---\ndescription: >\n  This is a long description\n  that spans multiple lines\n  and should be folded.\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        desc = fm.get("description", "")
        assert "long description" in desc
        assert "folded" in desc

    def test_literal_block_scalar_pipe(self):
        """YAML literal block scalar (|) preserves content."""
        content = "---\ndescription: |\n  Step 1: Do something\n  Step 2: Done\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        desc = fm.get("description", "")
        assert "Step 1" in desc
        assert "Step 2" in desc

    def test_quoted_values(self):
        """Double-quoted and single-quoted values."""
        content = "---\nname: \"Quoted Name\"\nversion: '1.0'\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        assert fm.get("name") == "Quoted Name"
        assert fm.get("version") == "1.0"

    def test_chinese_values(self):
        """Chinese text in values."""
        content = "---\nname: 任务规划引擎\nsummary: 结构化任务拆解与排程\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        assert "任务" in fm.get("name", "")
        assert "拆解" in fm.get("summary", "")

    def test_comment_lines_ignored(self):
        """YAML comment lines should be skipped."""
        content = "---\n# This is a comment\nname: Test\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        assert fm.get("name") == "Test"
        assert "# This is a comment" not in str(fm.values())

    def test_only_closing_delimiter(self):
        """Content with --- only at the end should not be treated as frontmatter."""
        content = "Some text\n---"
        fm, body = parse_yaml_frontmatter(content)
        assert fm == {}
        assert body == content

    def test_frontmatter_with_blank_lines(self):
        """Frontmatter containing blank lines between key-value pairs."""
        content = "---\nname: Test\n\nversion: 1.0\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        assert fm.get("name") == "Test"
        assert fm.get("version") == "1.0"

    def test_multiline_scalar_with_list_boundary(self):
        """Folded scalar followed by a list item should stop the scalar correctly."""
        content = "---\ndescription: >\n  A long description\n  on multiple lines\n- list_item\n---\n# Hello"
        fm, body = parse_yaml_frontmatter(content)
        desc = fm.get("description", "")
        assert "long description" in desc
