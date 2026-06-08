---
name: SkillFather
description: |
  Multi-Platform Agent Skill 适配度分析工具。
  从使用角度分析一个 Agent Skill 是否适用，基于 Skill 的定义文件自动生成 6-10 个诊断问题，
  输出 5 维度适配度评分（满分 10 分）。
  支持 WorkBuddy、CodeBuddy、Codex、Claude Code、Coze、Hermes Agent 六大平台。
  仅做适用性评审，不对安全性负责。
version: 0.2.1
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
- 安装后命令 `python -m skillfather` 可用

---

## 核心流程：选择分析模式

当用户要求分析某个 Skill 时，Agent **必须**先让用户选择分析模式，再执行对应的流程。

**Step 0：确定 Skill 文件路径**
- 如果用户提供了 Skill 路径（文件或目录），直接使用
- 如果用户引用了 `@skill:xxx`，从 WorkBuddy skills 目录查找：`~/.workbuddy/skills/xxx/SKILL.md`
- 如果用户提供 GitHub URL，提示用户先 clone 到本地

**Step 1：让用户选择分析模式**

使用 AskUserQuestion 工具向用户展示以下选项：

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| **基于记忆分析** | Agent 结合自身记忆（已装技能、工具环境、用户画像）个性化解读评分 | 想要最贴合自己的分析结果 |
| **交互分析** | Agent 逐题提问，用户根据实际情况回答，得到精确评分 | 首次分析、需要深度了解 |
| **自动分析** | 基于 Skill 内容特征自动估算评分，快速出结果 | 快速预览、不需要个性化 |

**Step 2：根据用户选择执行对应流程**

---

### 模式一：基于记忆分析

此模式利用 Agent 自身的记忆和上下文来个性化解读评分。

**执行步骤：**

1. **收集上下文**：Agent 读取以下信息构建用户画像：
   - 读取 workspace 记忆文件 `.workbuddy/memory/MEMORY.md` 和当日日志
   - 列出用户已安装的技能（`~/.workbuddy/skills/` 目录）
   - 检查用户常用的工具和环境（通过记忆中的偏好信息）
   - 读取 `~/.workbuddy/MEMORY.md` 获取跨项目偏好

2. **运行 CLI 分析**：
   ```bash
   python -m skillfather analyze <skill_path> --format console
   ```

3. **个性化解读**：Agent 基于收集到的上下文，对 CLI 输出的每个维度评分进行个性化解读：
   - **用例契合度**：结合用户日常工作内容（如 SAP 分析、前端开发等）判断该 Skill 是否匹配
   - **环境就绪度**：结合用户已装技能和工具，判断所需依赖是否就绪
   - **前置条件**：结合用户记忆中的配置信息（API Key、已连接的服务等）
   - **工作流匹配**：结合用户的工作习惯和已用工具链，判断是否融入
   - **文档质量**：Agent 自行评估文档的完整性和可操作性

4. **输出格式**：Agent 以 Markdown 表格 + 文字解读的方式呈现最终结论，每个维度给出：
   - 原始分数（CLI 输出）
   - 个性化调整理由（基于记忆）
   - 最终建议分数

5. **总结**：给出是否推荐安装的结论，以及需要特别注意的前置条件或适配事项

---

### 模式二：交互分析

此模式由 Agent 逐题提问，用户回答后计算精确评分。

**执行步骤：**

1. **运行 CLI 分析获取题目**：
   ```bash
   python -m skillfather analyze <skill_path> --format console
   ```
   记录 CLI 输出的所有诊断问题。

2. **逐题交互**：Agent 从 CLI 输出中提取每个诊断问题，使用 AskUserQuestion 逐题向用户提问：
   - 展示问题文本和解释
   - 选项固定为：`完全满足(y)` / `部分满足(p)` / `完全不满足(n)`
   - 也可以让用户输入 1-10 的具体数字

3. **计算评分**：Agent 根据用户回答重新计算各维度分数和总分：
   - 每题用户回答映射为 0.0-1.0 分：y=1.0, p=0.5, n=0.0, 数字=数字/10
   - 各维度分数 = 该维度题目加权平均
   - 总分 = 各维度加权求和（用例25% + 环境20% + 前置20% + 工作流20% + 文档15%）

4. **输出结果**：Agent 用 Markdown 表格展示最终评分，包括每个问题的用户回答和评分。

---

### 模式三：自动分析

此模式直接运行 CLI，基于 Skill 内容特征自动估算评分。

**执行步骤：**

1. **运行 CLI 分析**：
   ```bash
   python -m skillfather analyze <skill_path>
   ```

2. **可选输出格式**：
   ```bash
   # HTML 报告（推荐，可视化更好）
   python -m skillfather analyze <skill_path> --format html -o <output.html>

   # Markdown 报告
   python -m skillfather analyze <skill_path> --format markdown -o <output.md>

   # 同时输出所有格式
   python -m skillfather analyze <skill_path> --format all
   ```

3. **展示结果**：
   - 终端输出：直接展示给用户
   - HTML 报告：使用 `preview_url` 工具打开预览
   - Markdown 报告：直接展示或作为附件

---

## 平台指定

支持 `--platform` 参数指定分析平台：
```bash
python -m skillfather analyze <skill_path> --platform <platform>
```

| 平台 | `--platform` 值 |
|------|-----------------|
| WorkBuddy | `workbuddy` |
| CodeBuddy | `codebuddy` |
| OpenAI Codex | `codex` |
| Claude Code | `claude-code` |
| Coze | `coze` |
| Hermes Agent | `hermes` |
| 自动检测 | `auto`（默认） |

## 评分判读

| 分数段 | 判定 | 建议 |
|--------|------|------|
| 8.0-10.0 | RECOMMENDED | 强烈推荐安装 |
| 6.0-7.9 | CONDITIONAL | 可以安装，注意标注的前置条件 |
| 4.0-5.9 | CAUTION | 谨慎安装，可能需要较多适配 |
| 0.0-3.9 | NOT RECOMMENDED | 不推荐，与使用场景不匹配 |

## LLM 增强模式（可选）

设置环境变量后可用 `--llm` 模式获得更精准的问题生成：
```bash
set SKILLFATHER_API_KEY=sk-xxx
python -m skillfather analyze <skill_path> --llm
```

## 注意事项

- 本工具仅评估**适用性**（是否适合你的使用场景），不涉及安全性审计
- 规则引擎模式为离线零依赖分析，LLM 模式需要配置 API Key
- 自动检测平台可能不准确，如有疑问请手动指定 `--platform`

## 跨平台安装

仓库 `dist/` 目录包含各平台格式的 SkillFather 适配文件，可直接复制到对应平台使用：

| 平台 | 安装路径 | 文件 |
|------|---------|------|
| **WorkBuddy** | `~/.workbuddy/skills/skillfather/` | `SKILL.md`（项目根目录） |
| **CodeBuddy** | `~/.codebuddy/skills/skillfather/` | `dist/codebuddy/SKILL.md` |
| **Claude Code** | `~/.claude/commands/` | `dist/claude-code/skillfather.md` |
| **Codex** | `~/.agents/skills/skillfather/` | `dist/codex/SKILL.md` + `dist/codex/agents/openai.yaml` |
| **Hermes** | `~/.hermes/skills/productivity/skillfather/` | `dist/hermes/productivity/SKILL.md` |
| **Coze** | 不适用 | Coze 为 Web UI 平台，需手动在 Web 端创建 Bot |

### 安装示例

```bash
# Claude Code
cp dist/claude-code/skillfather.md ~/.claude/commands/skillfather.md

# Codex
cp -r dist/codex ~/.agents/skills/skillfather

# Hermes
cp -r dist/hermes/productivity/skillfather ~/.hermes/skills/productivity/skillfather

# CodeBuddy
cp dist/codebuddy/SKILL.md ~/.codebuddy/skills/skillfather/SKILL.md
```
