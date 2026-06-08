---
name: skillfather
description: |
  Multi-Platform Agent Skill 适配度分析工具。
  从使用角度分析一个 Agent Skill 是否适用，基于 Skill 的定义文件自动生成 6-10 个诊断问题，
  输出 5 维度适配度评分（满分 10 分）。
  支持 WorkBuddy、CodeBuddy、Codex、Claude Code、Coze、Hermes Agent 六大平台。
  仅做适用性评审，不对安全性负责。
version: 0.2.0
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

# SkillFather - Agent Skill 适配度分析工具

## 定位

SkillFather 从**使用角度**分析一个 Agent Skill 是否适用于当前用户。
仅做适用性评审，不对安全性负责。

## 前置条件

- Python 3.10+ 已安装
- 已执行 `pip install git+https://github.com/alpsmonkey/SkillFather.git`
- 验证安装：`python -m skillfather --version`

## 分析流程

**Step 1：确定 Skill 文件路径**
- 如果用户提供了路径，直接使用
- WorkBuddy: `~/.workbuddy/skills/<name>/SKILL.md`
- Claude Code: `.claude/commands/<name>.md`
- Codex: `.agents/skills/<name>/SKILL.md`

**Step 2：执行分析命令**

```bash
# 规则引擎模式（零配置）
python -m skillfather analyze <skill_path>

# 指定平台
python -m skillfather analyze <skill_path> --platform <platform>

# HTML 报告
python -m skillfather analyze <skill_path> --format html -o <output.html>

# Markdown 报告
python -m skillfather analyze <skill_path> --format markdown -o <output.md>

# 全部格式
python -m skillfather analyze <skill_path> --format all
```

**Step 3：展示结果**
- 终端输出：直接展示
- HTML 报告：使用 preview_url 预览
- Markdown 报告：内联展示或作为附件

## 评分判读

| 分数段 | 判定 | 建议 |
|--------|------|------|
| 8.0-10.0 | RECOMMENDED | 强烈推荐安装 |
| 6.0-7.9 | CONDITIONAL | 可以安装，注意前置条件 |
| 4.0-5.9 | CAUTION | 谨慎安装，可能需要较多适配 |
| 0.0-3.9 | NOT RECOMMENDED | 不推荐，与场景不匹配 |

## 注意事项

- 本工具仅评估**适用性**（是否适合你的使用场景），不涉及安全性审计
- 规则引擎模式为离线零依赖分析，LLM 模式需要配置 API Key
- 自动检测平台可能不准确，如有疑问请手动指定 `--platform`
