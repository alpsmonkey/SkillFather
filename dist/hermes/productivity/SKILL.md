---
name: skillfather
description: |
  Multi-Platform Agent Skill 适配度分析工具。
  从使用角度分析一个 Agent Skill 是否适用，基于 Skill 的定义文件自动生成 6-10 个诊断问题，
  输出 5 维度适配度评分（满分 10 分）。
  支持 WorkBuddy、CodeBuddy、Codex、Claude Code、Coze、Hermes Agent 六大平台。
  仅做适用性评审，不对安全性负责。
version: 0.2.1
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

## 核心流程：选择分析模式

**Step 0：确定 Skill 文件路径**

**Step 1：让用户选择分析模式**

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| **基于记忆分析** | Agent 结合自身记忆个性化解读评分 | 最贴合自己 |
| **交互分析** | Agent 逐题提问，用户回答 | 深度评估 |
| **自动分析** | 基于 Skill 内容特征自动估算 | 快速预览 |

**Step 2：根据选择执行**

### 模式一：基于记忆分析

1. Agent 读取记忆文件、已装技能、工具环境
2. 运行 `python -m skillfather analyze <skill_path>`
3. 基于上下文个性化解读每个维度评分
4. 输出 Markdown 表格 + 文字解读 + 最终推荐

### 模式二：交互分析

1. 运行 `python -m skillfather analyze <skill_path>` 获取题目
2. 逐题向用户提问（完全满足/部分满足/完全不满足）
3. 根据回答计算评分
4. 输出问题、回答、评分表格

### 模式三：自动分析

1. 运行 `python -m skillfather analyze <skill_path>`
2. 可选 `--format html|markdown|all`
3. 直接展示结果

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
