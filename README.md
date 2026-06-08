# SkillFit

**Multi-Platform Agent Skill 适配度分析工具**

在安装或使用一个 Agent Skill 之前，从使用角度分析它是否真的适合你——基于 5 个维度、6-10 个诊断问题，输出满分 10 分的适配度评分。

> **定位声明**：SkillFit 只做**适用性评审**（fitness/suitability assessment），从用户实际使用场景出发评估一个 Skill 是否适合安装和使用。**不涉及安全性审计、合规检查或代码漏洞分析。**

## 支持平台

| 平台 | Skill 格式 | 存储路径 |
|------|-----------|---------|
| **WorkBuddy** | SKILL.md (YAML + Markdown) | `~/.workbuddy/skills/` |
| **CodeBuddy** | SKILL.md (YAML + Markdown) | `~/.codebuddy/skills/` |
| **OpenAI Codex Agent** | SKILL.md + agents/openai.yaml | `.agents/skills/` |
| **Claude Code** | .claude/commands/*.md | `.claude/commands/` |
| **Coze / 扣子** | .skill / .zip / JSON | Web UI + 导出文件 |
| **Hermes Agent** | SKILL.md (Hermes metadata) | `~/.hermes/skills/` |

## 安装

```bash
# 克隆项目
git clone https://github.com/your-username/skillfit.git
cd skillfit

# 安装（零外部依赖）
pip install -e .
```

## 快速开始

```bash
# 列出所有支持的平台
skillfit platforms

# 自动检测平台并分析
skillfit analyze path/to/SKILL.md

# 指定平台
skillfit analyze path/to/command.md --platform claude-code

# 交互式问答（精确评分）
skillfit analyze path/to/SKILL.md --interactive

# 输出 HTML 报告
skillfit analyze path/to/SKILL.md --format html -o report.html

# LLM 增强模式
SKILLFIT_API_KEY=xxx skillfit analyze SKILL.md --llm --interactive
```

## 使用示例

### WorkBuddy / CodeBuddy Skill

```bash
skillfit analyze ~/.workbuddy/skills/my-skill/SKILL.md
skillfit analyze ~/.codebuddy/skills/pdf-editor/SKILL.md --platform codebuddy
```

### OpenAI Codex Skill

```bash
skillfit analyze ~/.agents/skills/deploy/SKILL.md --platform codex
```

### Claude Code 命令

```bash
skillfit analyze .claude/commands/review.md --platform claude-code
```

### Coze / 扣子 技能

```bash
skillfit analyze exported_skill.skill --platform coze
skillfit analyze bot_config.json --platform coze
```

### Hermes Agent 技能

```bash
skillfit analyze ~/.hermes/skills/research/arxiv/SKILL.md --platform hermes
```

## 评分维度

| 维度 | 权重 | 说明 |
|------|------|------|
| 用例契合度 | 25% | Skill 的触发场景是否覆盖你的实际需求 |
| 环境就绪度 | 20% | 你的 Agent 环境是否具备所需工具和依赖 |
| 前置条件 | 20% | 你是否满足 Skill 运行所需的先决条件 |
| 工作流匹配 | 20% | Skill 的工作流程是否符合你的操作习惯 |
| 文档质量 | 15% | Skill 的文档是否清晰、完整、易于理解 |

## 双模式引擎

| 模式 | 说明 | 依赖 |
|------|------|------|
| 规则引擎 | 基于模板的离线分析，零配置 | 无（纯 stdlib） |
| LLM 增强 | 使用大模型生成个性化问题和评分 | OpenAI 兼容 API |

## 项目结构

```
skillfit/
├── src/skillfit/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py              # CLI 入口（多平台支持）
│   ├── parser.py           # 通用 SKILL.md 解析器
│   ├── analyzer.py         # 分析引擎（规则 + LLM）
│   ├── reporter.py         # HTML / Markdown 报告
│   ├── config.py           # 配置管理
│   └── platforms/          # 多平台适配器
│       ├── __init__.py     # 平台注册与自动检测
│       ├── base.py         # 适配器基类
│       ├── workbuddy.py    # WorkBuddy
│       ├── codebuddy.py    # CodeBuddy
│       ├── codex.py        # OpenAI Codex Agent
│       ├── claude_code.py  # Claude Code
│       ├── coze.py         # Coze / 扣子
│       └── hermes.py       # Hermes Agent
├── templates/
│   └── report.html         # HTML 报告模板
├── examples/              # 各平台示例文件
│   ├── sample_skill.md         # WorkBuddy 示例
│   ├── sample_codex_skill.md   # Codex 示例
│   ├── sample_claude_command.md # Claude Code 示例
│   ├── sample_coze_skill.json  # Coze 示例
│   └── sample_hermes_skill.md  # Hermes 示例
├── tests/
│   └── test_parser.py
├── README.md
├── LICENSE
├── pyproject.toml
└── requirements.txt
```

## 配置

环境变量：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `SKILLFIT_API_KEY` | LLM API Key | 无（仅规则模式） |
| `SKILLFIT_API_BASE` | API Base URL | `https://api.openai.com/v1` |
| `SKILLFIT_MODEL` | LLM 模型名 | `gpt-4o-mini` |
| `SKILLFIT_CONFIG` | 配置文件路径 | 无 |

JSON 配置文件（可选）：

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

## License

MIT License
