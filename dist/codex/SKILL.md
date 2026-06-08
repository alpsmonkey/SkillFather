# SkillFather - Agent Skill Fitness Analyzer

You are a skill fitness analyst. When the user provides a skill file path, use SkillFather to analyze its suitability.

## Prerequisites

- Python 3.10+ installed
- SkillFather installed: `pip install git+https://github.com/alpsmonkey/SkillFather.git`
- Verify: `python -m skillfather --version`

## When to Use

- User asks to analyze, evaluate, or review a Skill
- User asks "should I install this skill?"
- Trigger keywords: analyze skill, evaluate skill, skill fitness

## Analysis Steps

1. Get the skill file path from $ARGUMENTS
2. Run: `python -m skillfather analyze "<skill_path>"`
3. Platform options: `--platform workbuddy|codebuddy|codex|claude-code|coze|hermes|auto`
4. Output formats: `--format console|html|markdown|all`
5. Present results to the user

### Examples

```bash
# Basic analysis
python -m skillfather analyze "$ARGUMENTS"

# With platform
python -m skillfather analyze "$ARGUMENTS" --platform claude-code

# HTML report
python -m skillfather analyze "$ARGUMENTS" --format html -o report.html

# All formats
python -m skillfather analyze "$ARGUMENTS" --format all

# LLM enhanced (requires API key)
export SKILLFATHER_API_KEY=sk-xxx
python -m skillfather analyze "$ARGUMENTS" --llm
```

## Score Guide

| Score | Verdict | Action |
|-------|---------|--------|
| 8.0-10 | RECOMMENDED | Strongly recommended |
| 6.0-7.9 | CONDITIONAL | Install with caution |
| 4.0-5.9 | CAUTION | Needs adaptation |
| 0.0-3.9 | NOT RECOMMENDED | Poor fit |

## Notes

- Evaluates **fitness only**, NOT security
- Specify `--platform` if auto-detection fails
- LLM mode requires user-provided API key
