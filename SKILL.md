---
name: SkillFather
description: |
  Multi-Platform Agent Skill 适配度分析工具。
  从使用角度分析一个 Agent Skill 是否适用，基于 Skill 的定义文件自动生成 6-10 个诊断问题，
  输出 5 维度适配度评分（满分 10 分）。
  支持 WorkBuddy、CodeBuddy、Codex、Claude Code、Coze、Hermes Agent 六大平台。
  仅做适用性评审，不对安全性负责。
version: 0.2.0
platforms:
  - workbuddy
  - codebuddy
  - codex
  - claude-code
  - coze
  - hermes
read_when:
  - 用户要求分析、评估、评审一个 Skill 是否适用
  - 用户提到适配度、适合度、fitness、fitness analysis
  - 用户想了解某个 Skill 安装前是否值得安装
  - 用户要求对比多个 Skill 的适用性
triggers:
  - 分析技能
  - 评审技能
  - 评估技能适用性
  - skill fitness
  - skill analysis
  - 适配度分析
  - 分析skill
  - skillfather
---

# SkillFather - Multi-Platform Agent Skill 适配度分析工具

## 定位

SkillFather 从**使用角度**分析一个 Agent Skill 是否适用于当前用户。
仅做适用性评审，不对安全性负责。

## 工作原理

1. 用户提供 Skill 文件路径（SKILL.md / .claude/commands/*.md / .skill / JSON / 目录）
2. SkillFather 解析 Skill 定义，提取触发词、工具依赖、前置条件、功能描述等
3. 基于 5 个维度生成 6-10 个诊断问题
4. 输出适配度评分（满分 10 分）+ 逐维度分析

## 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 用例契合度 | 25% | Skill 用途是否匹配用户工作场景 |
| 环境就绪度 | 20% | 所需工具、API、平台是否就绪 |
| 前置条件 | 20% | 依赖、配置、权限是否满足 |
| 工作流匹配 | 20% | 是否融入现有工作流程 |
| 文档质量 | 15% | README 完整度、可操作性 |

## 使用方式

SkillFather 是一个 Python CLI 工具，本技能指导 Agent 如何调用它。

### 前置条件

- Python 3.10+ 已安装
- 已执行 `pip install -e "E:\workspace\2026-06-08-08-32-31\skillfit"`（开发模式安装）
- 安装后 CLI 命令 `skillfather` 可用

### 基本用法

当用户要求分析某个 Skill 时，Agent 应执行以下步骤：

**Step 1：确定 Skill 文件路径**
- 如果用户提供了 Skill 路径（文件或目录），直接使用
- 如果用户引用了 `@skill:xxx`，从 WorkBuddy skills 目录查找：`~/.workbuddy/skills/xxx/SKILL.md`
- 如果用户提供 GitHub URL，提示用户先 clone 到本地

**Step 2：执行分析命令**

```bash
# 规则引擎模式（零配置）
python -m skillfather analyze <skill_path>

# 指定平台
python -m skillfather analyze <skill_path> --platform <platform>

# 生成 HTML 报告
python -m skillfather analyze <skill_path> --format html -o <output.html>

# 生成 Markdown 报告
python -m skillfather analyze <skill_path> --format markdown -o <output.md>

# 同时输出所有格式
python -m skillfather analyze <skill_path> --format all
```

**Step 3：展示结果**
- 终端输出：直接展示给用户
- HTML 报告：使用 `preview_url` 工具打开预览
- Markdown 报告：直接展示或作为附件

### 平台列表

```bash
python -m skillfather platforms
```

### 支持的平台与典型文件

| 平台 | 典型文件路径 | `--platform` 值 |
|------|-------------|-----------------|
| WorkBuddy | `~/.workbuddy/skills/<name>/SKILL.md` | `workbuddy` |
| CodeBuddy | `~/.codebuddy/skills/<name>/SKILL.md` | `codebuddy` |
| OpenAI Codex | `.agents/skills/<name>/SKILL.md` | `codex` |
| Claude Code | `.claude/commands/<name>.md` | `claude-code` |
| Coze | `<name>.skill` / `<name>.zip` / JSON | `coze` |
| Hermes Agent | `~/.hermes/skills/<cat>/<name>/SKILL.md` | `hermes` |

不指定 `--platform` 时自动检测。

### LLM 增强模式（可选）

设置环境变量后可用 `--llm` 模式获得更精准的分析：

```bash
# 需要 API Key
set SKILLFATHER_API_KEY=sk-xxx
python -m skillfather analyze <skill_path> --llm
```

## 输出格式

### 终端报告
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

### HTML 报告
带可视化的完整分析报告，使用 `preview_url` 预览。

### Markdown 报告
结构化的 Markdown 文本，适合归档和分享。

## 评分判读

| 分数段 | 判定 | 建议 |
|--------|------|------|
| 8.0-10.0 | RECOMMENDED | 强烈推荐安装 |
| 6.0-7.9 | CONDITIONAL | 可以安装，注意标注的前置条件 |
| 4.0-5.9 | CAUTION | 谨慎安装，可能需要较多适配 |
| 0.0-3.9 | NOT RECOMMENDED | 不推荐，与使用场景不匹配 |

## 注意事项

- 本工具仅评估**适用性**（是否适合你的使用场景），不涉及安全性审计
- 规则引擎模式为离线零依赖分析，LLM 模式需要配置 API Key
- 自动检测平台可能不准确，如有疑问请手动指定 `--platform`
