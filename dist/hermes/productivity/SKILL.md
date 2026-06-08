---
name: skillfather
description: |
  Multi-Platform Agent Skill 适配度分析工具。
  从使用角度分析一个 Agent Skill 是否适用，基于 Skill 的定义文件自动生成 6-10 个诊断问题，
  输出 5 维度适配度评分（满分 10 分）。
  支持 WorkBuddy、CodeBuddy、Codex、Claude Code、Coze、Hermes Agent 六大平台。
  仅做适用性评审，不对安全性负责。
version: 0.2.0
author: alpsmonkey
license: MIT
platforms: [macos, linux, windows]

metadata:
  hermes:
    tags: [skill, analysis, fitness, review, evaluation]
    category: productivity
    related_skills: [skill_manage]

required_environment_variables: []
required_credential_files: []
---

# SkillFather - Agent Skill 适配度分析工具

## When to Use

Use this skill when the user asks to analyze, evaluate, or review an Agent Skill's fitness/suitability. Triggers include:

- 分析技能 / 评审技能 / 评估技能适用性
- skill fitness / skill analysis / 适配度分析
- "should I install this skill?"
- Compare fitness of multiple skills

## Prerequisites

- Python 3.10+ installed
- SkillFather installed: `pip install git+https://github.com/alpsmonkey/SkillFather.git`
- Verify: `python -m skillfather --version`

## Analysis Steps

1. Get the skill file path from the user
2. Run SkillFather analysis

### Commands

```bash
# Basic analysis (rule engine, zero config)
python -m skillfather analyze <skill_path>

# Specify platform
python -m skillfather analyze <skill_path> --platform <platform>

# HTML report
python -m skillfather analyze <skill_path> --format html -o report.html

# Markdown report
python -m skillfather analyze <skill_path> --format markdown -o report.md

# All formats
python -m skillfather analyze <skill_path> --format all

# LLM enhanced (requires API key)
export SKILLFATHER_API_KEY=sk-xxx
python -m skillfather analyze <skill_path> --llm
```

Supported platforms: `workbuddy`, `codebuddy`, `codex`, `claude-code`, `coze`, `hermes`, `auto`

## Presenting Results

- Terminal output: display directly
- HTML report: use preview mechanism to show
- Markdown report: display inline or as attachment

## Score Guide

| Score | Verdict | Action |
|-------|---------|--------|
| 8.0-10.0 | RECOMMENDED | Strongly recommended |
| 6.0-7.9 | CONDITIONAL | Install with caution |
| 4.0-5.9 | CAUTION | Needs significant adaptation |
| 0.0-3.9 | NOT RECOMMENDED | Poor fit for use case |

## Important

- This tool evaluates **fitness/suitability only** - NOT security
- Auto-detection may be inaccurate; specify `--platform` if in doubt
- LLM mode requires user-provided API key (SKILLFATHER_API_KEY)
