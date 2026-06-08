<p align="center">
  <img src="docs/logo.svg" alt="SkillFather" width="360" />
</p>

<h2 align="center">SkillFather</h2>

<p align="center">
  <b>Multi-Platform Agent Skill Fitness Analyzer</b>
</p>

<p align="center">
  <a href="README.md">English</a> · <a href="docs/README_CN.md">简体中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-v0.2.1-orange" alt="Version" />
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="License" />
  <img src="https://img.shields.io/badge/platforms-6-green" alt="Platforms" />
</p>

<p align="center">
  <b>Don't install a skill just because it looks cool — find out if it's actually built for <i>you</i>.</b>
</p>

---

> **Scope Statement**: SkillFather focuses exclusively on **fitness/suitability assessment** — evaluating whether a Skill matches your actual use cases. It does **not** perform security audits, compliance checks, or vulnerability analysis.

## What it does

Every Agent platform has a marketplace full of Skills. Some are brilliant — for someone else. SkillFather reads a Skill definition, asks you the right questions, and scores it across 5 dimensions so you know **before installing** whether it's worth your time.

```
SKILL.md → Parse → Generate 6-10 Diagnostic Questions → 5-Dimension Score → Fit Rating /10
```

### The 5 Dimensions

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Use-Case Fit | 25% | Does the Skill's trigger scope cover your actual needs? |
| Environment Readiness | 20% | Do you have the required tools, connectors, and dependencies? |
| Prerequisites | 20% | Do you meet the Skill's preconditions and access requirements? |
| Workflow Match | 20% | Does the Skill's execution flow match how you actually work? |
| Documentation Quality | 15% | Is the Skill's documentation clear, complete, and actionable? |

### Supported Platforms

| Platform | Skill Format | Storage Path |
|----------|-------------|--------------|
| **WorkBuddy** | SKILL.md (YAML + Markdown) | `~/.workbuddy/skills/` |
| **CodeBuddy** | SKILL.md (YAML + Markdown) | `~/.codebuddy/skills/` |
| **OpenAI Codex Agent** | SKILL.md + agents/openai.yaml | `.agents/skills/` |
| **Claude Code** | .claude/commands/*.md | `.claude/commands/` |
| **Coze** | .skill / .zip / JSON | Web UI + exported files |
| **Hermes Agent** | SKILL.md (Hermes metadata) | `~/.hermes/skills/` |

## Quick Start

```bash
# Clone and install (zero external dependencies)
git clone https://github.com/alpsmonkey/SkillFather.git
cd SkillFather
pip install -e .
```

### Basic Usage

安装为 Agent 技能后，直接用自然语言触发即可，无需手动运行命令：

```
帮我分析一下这个技能
帮我分析一下这个skill
分析这个技能
分析这个skill
分析技能 / 评审技能 / 适配度分析
```

也可以通过命令行直接调用：

```bash
# List all supported platforms
skillfather platforms

# Auto-detect platform and analyze
skillfather analyze path/to/SKILL.md

# Specify a platform explicitly
skillfather analyze path/to/command.md --platform claude-code

# Interactive Q&A mode (get a personalized score)
skillfather analyze path/to/SKILL.md --interactive

# Output HTML report
skillfather analyze path/to/SKILL.md --format html -o report.html

# Output Markdown report
skillfather analyze path/to/SKILL.md --format markdown -o report.md
```

### Platform-Specific Examples

```bash
# WorkBuddy / CodeBuddy
skillfather analyze ~/.workbuddy/skills/my-skill/SKILL.md
skillfather analyze ~/.codebuddy/skills/pdf-editor/SKILL.md --platform codebuddy

# OpenAI Codex Agent
skillfather analyze .agents/skills/deploy/SKILL.md --platform codex

# Claude Code
skillfather analyze .claude/commands/review.md --platform claude-code

# Coze / 扣子
skillfather analyze exported_skill.json --platform coze

# Hermes Agent
skillfather analyze ~/.hermes/skills/research/SKILL.md --platform hermes
```

## Dual-Engine Architecture

| Mode | Description | Dependencies |
|------|-------------|---------------|
| **Rule Engine** | Template-based offline analysis, zero config | None (pure stdlib) |
| **LLM Enhanced** | Uses an LLM to generate personalized questions and scoring | Any OpenAI-compatible API |

### LLM Mode (Optional)

```bash
# Set API key via environment variable
export SKILLFATHER_API_KEY=sk-xxx
skillfather analyze SKILL.md --llm --interactive

# Or use a custom API endpoint
export SKILLFATHER_API_BASE=https://api.deepseek.com/v1
export SKILLFATHER_MODEL=deepseek-chat
skillfather analyze SKILL.md --llm --interactive
```

## Output Formats

### Terminal

```
╔══════════════════════════════════════════════════╗
║  SkillFather — Fitness Analysis Report          ║
╠══════════════════════════════════════════════════╣
║  Skill:   SAP Cost Analysis                      ║
║  Platform: workbuddy                             ║
║  Score:   7.2 / 10                              ║
║  Verdict: RECOMMENDED                            ║
╠══════════════════════════════════════════════════╣
║  Use-Case Fit       ████████░░  8.0/10          ║
║  Environment        ██████░░░░  6.0/10          ║
║  Prerequisites      ███████░░░  7.0/10          ║
║  Workflow Match     ████████░░  7.5/10          ║
║  Documentation      ███████░░░  7.0/10          ║
╚══════════════════════════════════════════════════╝
```

### HTML Report

Generate a styled, responsive HTML report with visual score breakdowns:

```bash
skillfather analyze SKILL.md --format html -o report.html
```

### Markdown Report

For note-taking or sharing:

```bash
skillfather analyze SKILL.md --format markdown -o report.md
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SKILLFATHER_API_KEY` | LLM API Key | None (rule mode only) |
| `SKILLFATHER_API_BASE` | API Base URL | `https://api.openai.com/v1` |
| `SKILLFATHER_MODEL` | LLM model name | `gpt-4o-mini` |
| `SKILLFATHER_CONFIG` | Config file path | None |

### JSON Config (Optional)

Create `skillfather.json` in your project root or specify via `SKILLFATHER_CONFIG`:

```json
{
  "llm": {
    "enabled": true,
    "api_key": "sk-xxx",
    "api_base": "https://api.openai.com/v1",
    "model": "gpt-4o-mini"
  },
  "analysis": {
    "num_questions": 10,
    "score_weights": {
      "use_case": 0.25,
      "environment": 0.2,
      "prerequisites": 0.2,
      "workflow": 0.2,
      "documentation": 0.15
    }
  }
}
```

## Project Structure

```
SkillFather/
├── src/skillfather/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # CLI entry point (multi-platform)
│   ├── parser.py           # Universal Skill parser
│   ├── analyzer.py         # Analysis engine (rule + LLM)
│   ├── reporter.py         # HTML / Markdown reports
│   ├── config.py           # Configuration management
│   └── platforms/          # Platform adapters
│       ├── __init__.py     # Platform registry & auto-detection
│       ├── base.py         # Adapter base class
│       ├── workbuddy.py    # WorkBuddy
│       ├── codebuddy.py    # CodeBuddy
│       ├── codex.py        # OpenAI Codex Agent
│       ├── claude_code.py  # Claude Code
│       ├── coze.py         # Coze
│       └── hermes.py       # Hermes Agent
├── templates/
│   └── report.html         # HTML report template
├── examples/              # Sample files per platform
│   ├── sample_skill.md
│   ├── sample_codex_skill.md
│   ├── sample_claude_command.md
│   ├── sample_coze_skill.json
│   └── sample_hermes_skill.md
├── tests/
│   └── test_parser.py
├── dist/                    # Platform-specific SkillFather skill files
│   ├── claude-code/
│   │   └── skillfather.md   # ~/.claude/commands/skillfather.md
│   ├── codebuddy/
│   │   └── SKILL.md         # ~/.codebuddy/skills/skillfather/
│   ├── codex/
│   │   ├── SKILL.md         # ~/.agents/skills/skillfather/
│   │   └── agents/
│   │       └── openai.yaml
│   └── hermes/
│       └── productivity/
│           └── SKILL.md     # ~/.hermes/skills/productivity/skillfather/
├── SKILL.md                 # WorkBuddy skill definition (also used as root)
├── docs/
│   └── README_CN.md        # Chinese README
├── README.md
├── LICENSE
├── pyproject.toml
└── requirements.txt
```

## Use as a Skill on Your Platform

SkillFather can be installed as a native skill on most major Agent platforms:

```bash
# Claude Code - slash command
cp dist/claude-code/skillfather.md ~/.claude/commands/skillfather.md

# CodeBuddy
cp dist/codebuddy/SKILL.md ~/.codebuddy/skills/skillfather/SKILL.md

# Codex (OpenAI Agent)
cp -r dist/codex ~/.agents/skills/skillfather

# Hermes Agent
cp -r dist/hermes/productivity/skillfather ~/.hermes/skills/productivity/skillfather

# WorkBuddy
cp SKILL.md ~/.workbuddy/skills/skillfather/SKILL.md
```

> **Note:** Coze is a web-based platform — create a Bot manually via the Coze UI.

## Why "Father"?

Every Skill has a creator, but nobody tells you whether that Skill was built for **you**. SkillFather is the judge — it reads the fine print, asks the hard questions, and gives you a number you can trust.

> Install smarter. Not more.

## License

[MIT](LICENSE) — use it, modify it, ship it.
