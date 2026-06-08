---
description: "Analyze any Agent Skill's fitness/suitability before installing. Generates 6-10 diagnostic questions across 5 dimensions and outputs a suitability score (0-10). Supports 6 platforms: WorkBuddy, CodeBuddy, Codex, Claude Code, Coze, Hermes Agent."
allowed-tools: ["Bash(python*)", "Bash(pip*)", "Read"]
---

# SkillFather - Agent Skill Fitness Analyzer

You are a skill fitness analyst. When the user provides a skill file or directory path, use the SkillFather tool to analyze its suitability.

## Prerequisites

- Python 3.10+ is installed
- SkillFather is installed: `pip install git+https://github.com/alpsmonkey/SkillFather.git`
- Verify installation: `python -m skillfather --version`

## When to Use

- User asks to analyze, evaluate, or review a Skill's fitness/suitability
- User asks "is this skill worth installing?"
- User wants to compare multiple skills
- Trigger: analyze skill, evaluate skill, skill fitness, 适配度分析

## How to Analyze

**Step 1**: Get the skill file path from the user:
- If `$ARGUMENTS` is provided, use it as the path
- If user references a Claude Code skill, it's at `.claude/commands/<name>.md`
- If user references a WorkBuddy skill, it's at `~/.workbuddy/skills/<name>/SKILL.md`

**Step 2**: Run the analysis:

```bash
# Rule engine (zero config)
python -m skillfather analyze "$ARGUMENTS"

# Specify platform explicitly
python -m skillfather analyze "$ARGUMENTS" --platform <platform>

# Generate HTML report
python -m skillfather analyze "$ARGUMENTS" --format html -o skillfather_report.html

# Generate Markdown report
python -m skillfather analyze "$ARGUMENTS" --format markdown -o skillfather_report.md

# All formats at once
python -m skillfather analyze "$ARGUMENTS" --format all
```

Supported `--platform` values: `workbuddy`, `codebuddy`, `codex`, `claude-code`, `coze`, `hermes`, `auto`

**Step 3**: Present the results:
- Terminal output: display directly
- HTML report: use `preview_url` to show
- Markdown report: display inline or as attachment

## LLM Mode (Optional)

For deeper analysis, set API key first:
```bash
export SKILLFATHER_API_KEY=sk-xxx
python -m skillfather analyze "$ARGUMENTS" --llm
```

## Score Guide

| Score | Verdict | Action |
|-------|---------|--------|
| 8.0-10.0 | RECOMMENDED | Strongly recommended |
| 6.0-7.9 | CONDITIONAL | Install with caution |
| 4.0-5.9 | CAUTION | May need significant adaptation |
| 0.0-3.9 | NOT RECOMMENDED | Poor fit for your use case |

## Important

- This tool evaluates **fitness/suitability only** - NOT security
- Auto-detection may be inaccurate; specify `--platform` if in doubt
- For LLM mode, the user must provide their own API key
