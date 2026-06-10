"""Unit tests for the CLI module — argument parsing and basic command routing."""

import pytest
import tempfile
import os
from pathlib import Path
from skillfather.cli import main, _parse_score_input


def _write_tmp(content: str, suffix: str = ".md") -> str:
    """Write content to a temp file and return its path."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return f.name


class TestParseScoreInput:
    """Test _parse_score_input — interactive score parsing."""

    def test_yes_inputs(self):
        assert _parse_score_input("y") == 1.0
        assert _parse_score_input("yes") == 1.0
        assert _parse_score_input("是") == 1.0
        assert _parse_score_input("1") == 1.0

    def test_no_inputs(self):
        assert _parse_score_input("n") == 0.0
        assert _parse_score_input("no") == 0.0
        assert _parse_score_input("否") == 0.0
        assert _parse_score_input("0") == 0.0

    def test_partial_inputs(self):
        assert _parse_score_input("p") == 0.5
        assert _parse_score_input("partial") == 0.5
        assert _parse_score_input("部分") == 0.5
        assert _parse_score_input("0.5") == 0.5

    def test_numeric_0_to_10(self):
        assert _parse_score_input("5") == 0.5
        assert _parse_score_input("10") == 1.0
        assert _parse_score_input("3") == 0.3

    def test_invalid_inputs(self):
        assert _parse_score_input("abc") is None
        assert _parse_score_input("") is None
        assert _parse_score_input("11") is None  # out of range

    def test_case_insensitive(self):
        assert _parse_score_input("Y") == 1.0
        assert _parse_score_input("N") == 0.0
        assert _parse_score_input("P") == 0.5


class TestCLIArgParsing:
    """Test CLI argument parsing and command routing."""

    def test_no_command_returns_0(self):
        """No subcommand should print help and return 0."""
        result = main([])
        assert result == 0

    def test_version_flag(self):
        """--version should exit with version string."""
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0

    def test_analyze_missing_file(self):
        """analyze with non-existent file should sys.exit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            main(["analyze", "/nonexistent/SKILL.md"])
        assert exc_info.value.code == 1

    def test_analyze_with_valid_file(self):
        """analyze with a valid file should succeed (return 0)."""
        path = _write_tmp("---\nname: CLI Test\n---\n# CLI Test\n\nSome content here.\n")
        try:
            result = main(["analyze", path, "-f", "console"])
            assert result == 0
        finally:
            os.unlink(path)

    def test_analyze_html_output(self):
        """analyze with -f html should produce an HTML file."""
        path = _write_tmp("---\nname: HTML Test\n---\n# HTML Test\n\nContent.\n")
        out = tempfile.mktemp(suffix=".html")
        try:
            result = main(["analyze", path, "-f", "html", "-o", out])
            assert result == 0
            assert Path(out).exists()
            content = Path(out).read_text(encoding="utf-8")
            assert "HTML Test" in content or "html" in content.lower()
        finally:
            os.unlink(path)
            if Path(out).exists():
                os.unlink(out)

    def test_analyze_markdown_output(self):
        """analyze with -f markdown should produce a Markdown file."""
        path = _write_tmp("---\nname: MD Test\n---\n# MD Test\n\nContent.\n")
        out = tempfile.mktemp(suffix=".md")
        try:
            result = main(["analyze", path, "-f", "markdown", "-o", out])
            assert result == 0
        finally:
            os.unlink(path)
            if Path(out).exists():
                os.unlink(out)

    def test_platforms_command(self):
        """platforms subcommand should return 0."""
        result = main(["platforms"])
        assert result == 0

    def test_platform_auto_flag(self):
        """analyze --platform auto with valid file should not crash."""
        path = _write_tmp("---\nname: Auto Test\n---\n# Auto Test\n\nContent.\n")
        try:
            result = main(["analyze", path, "-p", "auto", "-f", "console"])
            assert result == 0
        finally:
            os.unlink(path)
