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

## Core Flow: Choose Analysis Mode

**Step 0**: Get the skill file path from the user:
- If `$ARGUMENTS` is provided, use it as the path
- If user references a Claude Code skill, it's at `.claude/commands/<name>.md`
- If user references a WorkBuddy skill, it's at `~/.workbuddy/skills/<name>/SKILL.md`

**Step 1**: Ask the user to choose an analysis mode. Present these options:

| Mode | Description | Best For |
|------|-------------|----------|
| **Memory-based Analysis** | Agent combines its memory (installed skills, tools, user profile) to personalize score interpretation | Most personalized result |
| **Interactive Analysis** | Agent asks each question one by one, user answers based on actual situation | First-time analysis, deep evaluation |
| **Auto Analysis** | CLI auto-estimates scores from Skill content features | Quick preview, no personalization needed |

**Step 2**: Execute the chosen mode's workflow.

---

### Mode 1: Memory-based Analysis

1. **Gather context**: Read your memory files, list installed skills, check user's tool environment
2. **Run CLI**: `python -m skillfather analyze "<skill_path>"`
3. **Personalize interpretation**: For each dimension, adjust the CLI output based on what you know about the user:
   - Use-case Fit: Does this skill match the user's daily work?
   - Environment Readiness: Are the required tools/dependencies already installed?
   - Prerequisites: Are API keys and configs already set up?
   - Workflow Match: Does it fit into the user's existing tool chain?
   - Documentation: Your own assessment of doc quality
4. **Output**: Markdown table with original score, personalization rationale, and final recommendation

### Mode 2: Interactive Analysis

1. **Run CLI to get questions**: `python -m skillfather analyze "<skill_path>"`
2. **Extract diagnostic questions** from the CLI output
3. **Ask each question** to the user one by one:
   - Options: `Fully meets (y)` / `Partially meets (p)` / `Does not meet (n)`
   - Or let user enter a 1-10 number
4. **Calculate scores** based on user answers (y=1.0, p=0.5, n=0.0, number/10)
5. **Output**: Markdown table showing each question, user's answer, and score

### Mode 3: Auto Analysis

1. **Run CLI**: `python -m skillfather analyze "<skill_path>"`
2. **Optional formats**: `--format html|markdown|all`
3. **Present results**: Display terminal output directly; use preview for HTML

---

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
- For LLM mode, the user must provide their own API key (SKILLFATHER_API_KEY)
