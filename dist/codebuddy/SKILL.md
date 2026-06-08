---
name: skillfather
description: |
  Multi-Platform Agent Skill 适配度分析工具。
  从使用角度分析一个 Agent Skill 是否适用，基于 Skill 的定义文件自动生成 6-10 个诊断问题，
  输出 5 维度适配度评分（满分 10 分）。
  支持 WorkBuddy、CodeBuddy、Codex、Claude Code、Coze、Hermes Agent 六大平台。
  仅做适用性评审，不对安全性负责。
version: 0.2.1
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
  - 帮我分析一下这个技能
  - 帮我分析一下这个skill
  - 分析这个skill
  - 分析这个技能
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

## 核心流程：选择分析模式

**Step 0：确定 Skill 文件路径**
- 如果用户提供了路径，直接使用
- WorkBuddy: `~/.workbuddy/skills/<name>/SKILL.md`
- Claude Code: `.claude/commands/<name>.md`
- Codex: `.agents/skills/<name>/SKILL.md`

**Step 1：让用户选择分析模式**

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| **基于记忆分析** | Agent 结合自身记忆（已装技能、工具环境、用户画像）个性化解读评分 | 想要最贴合自己的分析结果 |
| **交互分析** | Agent 逐题提问，用户根据实际情况回答，得到精确评分 | 首次分析、需要深度了解 |
| **自动分析** | 基于 Skill 内容特征自动估算评分，快速出结果 | 快速预览、不需要个性化 |

**Step 2：根据用户选择执行对应流程**

### 模式一：基于记忆分析

1. **收集上下文**：Agent 读取记忆文件（`.workbuddy/memory/`）、已装技能列表（`~/.workbuddy/skills/`）、用户工具环境偏好
2. **运行 CLI 分析**：`python -m skillfather analyze <skill_path>`
3. **个性化解读**：基于收集到的上下文，对每个维度评分进行个性化调整和解读
4. **输出**：Markdown 表格 + 文字解读，给出最终推荐结论

### 模式二：交互分析

1. **运行 CLI 获取题目**：`python -m skillfather analyze <skill_path>`
2. **逐题交互**：从输出中提取诊断问题，逐题向用户提问（完全满足/部分满足/完全不满足）
3. **计算评分**：根据用户回答计算各维度分数和总分
4. **输出**：Markdown 表格展示每个问题的用户回答和评分

### 模式三：自动分析

1. **运行 CLI**：`python -m skillfather analyze <skill_path>`
2. **可选格式**：`--format html|markdown|all`
3. **展示结果**：直接展示 / preview_url 预览 HTML

## 评分判读

| 分数段 | 判定 | 建议 |
|--------|------|------|
| 8.0-10.0 | RECOMMENDED | 强烈推荐安装 |
| 6.0-7.9 | CONDITIONAL | 可以安装，注意前置条件 |
| 4.0-5.9 | CAUTION | 谨慎安装，可能需要较多适配 |
| 0.0-3.9 | NOT RECOMMENDED | 不推荐，与场景不匹配 |

## 注意事项

- 本工具仅评估**适用性**，不涉及安全性审计
- 自动检测平台可能不准确，如有疑问请手动指定 `--platform`
- LLM 模式需要配置 SKILLFATHER_API_KEY
