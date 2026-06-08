"""Core analysis engine - generates questions and calculates adaptability scores."""

import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from typing import Optional
from skillfather.parser import parse_skill, SkillProfile
from skillfather.config import LLMConfig, AnalysisConfig


@dataclass
class Question:
    """A single diagnostic question."""

    id: int
    text: str
    dimension: str  # use_case, environment, prerequisites, workflow, documentation
    dimension_label: str
    explanation: str  # Why this question matters
    weight: float = 1.0

    # Interactive answers
    answer: Optional[str] = None
    score: Optional[float] = None  # 0.0 - 1.0


@dataclass
class DimensionScore:
    """Score for a single analysis dimension."""

    key: str
    label: str
    score: float  # 0.0 - 1.0
    questions: list = field(default_factory=list)


@dataclass
class AnalysisResult:
    """Complete analysis result."""

    skill: SkillProfile
    questions: list = field(default_factory=list)
    dimension_scores: list = field(default_factory=list)
    overall_score: float = 0.0  # 0.0 - 10.0
    recommendation: str = ""
    details: str = ""


# ── Rule-based question templates ──────────────────────────────────────

_TEMPLATES: list[dict] = [
    {
        "dimension": "use_case",
        "label": "用例契合度",
        "check_fn": "_check_use_case",
        "primary": {
            "condition": "has_triggers",
            "text": "你当前的工作是否涉及「{triggers}」这类场景？",
            "explanation": "该 Skill 的核心触发场景是否覆盖了你的实际需求。如果完全不匹配，说明这个 Skill 解决的不是你的问题。",
        },
        "fallback": {
            "condition": "always",
            "text": "这个 Skill 的定位（{summary}）与你的核心工作方向是否一致？",
            "explanation": "Skill 的整体定位决定了它的适用范围。定位偏离意味着即使安装了也很难用到。",
        },
    },
    {
        "dimension": "environment",
        "label": "环境就绪度",
        "check_fn": "_check_environment",
        "primary": {
            "condition": "has_tools",
            "text": "你的 WorkBuddy 环境中是否已安装/配置了以下工具：{tools}？",
            "explanation": "该 Skill 依赖特定的 MCP 工具或连接器。缺少这些依赖会导致 Skill 无法正常执行。",
        },
        "fallback": {
            "condition": "always",
            "text": "该 Skill 的运行环境（{summary}）是否与你当前的 WorkBuddy 配置兼容？",
            "explanation": "运行时依赖是 Skill 正常工作的基础。环境不匹配会导致安装后无法使用。",
        },
    },
    {
        "dimension": "prerequisites",
        "label": "前置条件",
        "check_fn": "_check_prerequisites",
        "primary": {
            "condition": "has_requirements",
            "text": "你是否满足该 Skill 的前置条件：{requirements}？",
            "explanation": "前置条件不满足意味着 Skill 执行时会中断或产生错误结果。",
        },
        "fallback": {
            "condition": "always",
            "text": "该 Skill（{summary}）是否要求你具备特定的专业知识或系统访问权限？",
            "explanation": "专业知识门槛和系统权限是常见的隐性前置条件，容易被忽略。",
        },
    },
    {
        "dimension": "workflow",
        "label": "工作流匹配",
        "check_fn": "_check_workflow",
        "primary": {
            "condition": "has_capabilities",
            "text": "该 Skill 的能力范围（{capabilities}）是否覆盖了你需要自动化的环节？",
            "explanation": "Skill 的能力边界决定了它能帮你做什么。能力缺口意味着你需要手动补充。",
        },
        "fallback": {
            "condition": "always",
            "text": "该 Skill 的工作流程（共 {line_count} 行指令）是否符合你的操作习惯和预期？",
            "explanation": "Skill 的指令逻辑决定了它如何替你完成任务。流程不匹配可能导致结果不符合预期。",
        },
    },
    {
        "dimension": "documentation",
        "label": "文档质量",
        "check_fn": "_check_documentation",
        "primary": {
            "condition": "has_sections",
            "text": "该 Skill 的文档结构是否清晰？共 {section_count} 个章节，是否包含完整的说明？",
            "explanation": "文档质量直接影响你理解和调试 Skill 的效率。模糊的文档意味着遇到问题时难以排查。",
        },
        "fallback": {
            "condition": "always",
            "text": "该 Skill 是否提供了足够的使用示例和边界条件说明？",
            "explanation": "没有示例和边界说明的 Skill，在实际使用中容易踩坑且难以复用。",
        },
    },
]


def _check_use_case(profile: SkillProfile) -> dict:
    return {
        "has_triggers": len(profile.triggers) > 0,
        "has_summary": bool(profile.summary or profile.description),
    }


def _check_environment(profile: SkillProfile) -> dict:
    return {
        "has_tools": len(profile.tools_required) > 0,
        "has_dependencies": len(profile.dependencies) > 0 or "pip install" in profile.instructions.lower(),
    }


def _check_prerequisites(profile: SkillProfile) -> dict:
    return {
        "has_requirements": len(profile.requirements) > 0,
        "has_read_when": len(profile.read_when) > 0,
    }


def _check_workflow(profile: SkillProfile) -> dict:
    line_count = len(profile.instructions.split("\n"))
    return {
        "has_instructions": line_count > 5,
        "has_capabilities": len(profile.capabilities) > 0,
    }


def _check_documentation(profile: SkillProfile) -> dict:
    return {
        "has_sections": len(profile.all_sections) >= 2,
    }


_CHECK_FNS = {
    "_check_use_case": _check_use_case,
    "_check_environment": _check_environment,
    "_check_prerequisites": _check_prerequisites,
    "_check_workflow": _check_workflow,
    "_check_documentation": _check_documentation,
}


def generate_questions_rule_based(profile: SkillProfile, num_questions: int = 8) -> list[Question]:
    """Generate diagnostic questions using rule-based templates.

    This mode works offline without an LLM API key.
    Each dimension contributes 1-2 questions. Primary template is used if the
    condition matches; otherwise the fallback template is used.
    """
    questions: list[Question] = []
    qid = 0
    weights = AnalysisConfig().score_weights

    for tmpl_group in _TEMPLATES:
        dim = tmpl_group["dimension"]
        label = tmpl_group["label"]
        check_fn = _CHECK_FNS.get(tmpl_group["check_fn"], lambda p: {})
        checks = check_fn(profile)

        # Pick primary if condition matches, otherwise fallback
        primary = tmpl_group["primary"]
        fallback = tmpl_group["fallback"]

        # Generate primary question
        if checks.get(primary["condition"], primary["condition"] == "always"):
            qid += 1
            text = primary["text"].format(
                triggers=profile.trigger_text[:60],
                summary=(profile.summary or profile.description)[:80],
                tools=profile.tool_text[:60],
                requirements=profile.requirement_text[:60],
                read_when="；".join(profile.read_when[:5]) if profile.read_when else "未指定",
                line_count=len(profile.instructions.split("\n")),
                capabilities=profile.capability_text[:60],
                section_count=len(profile.all_sections),
            )
            questions.append(Question(
                id=qid,
                text=text,
                dimension=dim,
                dimension_label=label,
                explanation=primary["explanation"],
                weight=weights.get(dim, 0.2),
            ))

        # Generate fallback question (second question per dimension)
        qid += 1
        text = fallback["text"].format(
            triggers=profile.trigger_text[:60],
            summary=(profile.summary or profile.description)[:80],
            tools=profile.tool_text[:60],
            requirements=profile.requirement_text[:60],
            read_when="；".join(profile.read_when[:5]) if profile.read_when else "未指定",
            line_count=len(profile.instructions.split("\n")),
            capabilities=profile.capability_text[:60],
            section_count=len(profile.all_sections),
        )
        questions.append(Question(
            id=qid,
            text=text,
            dimension=dim,
            dimension_label=label,
            explanation=fallback["explanation"],
            weight=weights.get(dim, 0.2),
        ))

        if qid >= num_questions:
            return questions[:num_questions]

    return questions[:num_questions]


def generate_questions_llm(profile: SkillProfile, config: LLMConfig, num_questions: int = 8) -> list[Question]:
    """Generate diagnostic questions using an LLM.

    This mode requires an OpenAI-compatible API key.
    """
    system_prompt = """你是一个 WorkBuddy SKILL 适配度分析专家。你的任务是从使用者的角度，基于 SKILL.md 的内容，生成 6-10 个诊断性问题，帮助用户判断该 SKILL 是否适用于自己的工作场景。

要求：
1. 问题必须覆盖以下维度：
   - use_case（用例契合度）：该 Skill 解决的问题是否是用户的真实需求？
   - environment（环境就绪度）：用户是否具备该 Skill 所需的运行环境？
   - prerequisites（前置条件）：用户是否满足使用该 Skill 的先决条件？
   - workflow（工作流匹配）：该 Skill 的执行流程是否符合用户的操作习惯？
   - documentation（文档质量）：文档是否足够清晰、完整、可操作？
2. 每个问题必须附带 explanation（为什么这个问题重要）
3. 问题应具体、可回答，避免笼统的"你是否需要"式问题
4. 优先覆盖有实际信息的维度

请以 JSON 数组格式输出，每个元素包含：
- text: 问题文本
- dimension: 维度 key（use_case/environment/prerequisites/workflow/documentation）
- dimension_label: 维度中文标签
- explanation: 解释文本

只输出 JSON，不要其他内容。"""

    user_prompt = f"""请分析以下 SKILL.md 内容，生成 {num_questions} 个适配度诊断问题：

---
{profile.raw_content[:4000]}
---

该 Skill 的解析结果：
- 触发词：{profile.trigger_text}
- 前置条件：{profile.requirement_text}
- 工具依赖：{profile.tool_text}
- 功能描述：{profile.capability_text}
- 文档章节：{len(profile.all_sections)} 个

生成 {num_questions} 个问题："""

    response = _call_llm(system_prompt, user_prompt, config)

    try:
        parsed = json.loads(response)
        questions = []
        for i, item in enumerate(parsed):
            questions.append(Question(
                id=i + 1,
                text=item["text"],
                dimension=item.get("dimension", "use_case"),
                dimension_label=item.get("dimension_label", item.get("dimension", "")),
                explanation=item.get("explanation", ""),
                weight=AnalysisConfig().score_weights.get(item.get("dimension", "use_case"), 0.2),
            ))
        return questions[:num_questions]
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[WARNING] LLM response parse failed ({e}), falling back to rule-based mode.")
        return generate_questions_rule_based(profile, num_questions)


def _call_llm(system_prompt: str, user_prompt: str, config: LLMConfig) -> str:
    """Call OpenAI-compatible chat completion API."""
    import ssl

    url = f"{config.base_url.rstrip('/')}/chat/completions"
    payload = json.dumps({
        "model": config.model,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.api_key}",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    # Handle SSL for self-signed certs (common in corporate environments)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"].strip()
    except urllib.error.URLError as e:
        raise RuntimeError(f"LLM API call failed: {e}") from e
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected LLM response format: {e}") from e


def calculate_score(questions: list[Question]) -> float:
    """Calculate overall score from answered questions.

    Args:
        questions: List of questions with scores set (0.0-1.0).

    Returns:
        Overall score from 0.0 to 10.0.
    """
    if not questions:
        return 0.0

    total_weight = 0.0
    weighted_sum = 0.0

    for q in questions:
        if q.score is not None:
            total_weight += q.weight
            weighted_sum += q.score * q.weight

    if total_weight == 0:
        return 0.0

    return round(weighted_sum / total_weight * 10, 1)


def calculate_dimension_scores(questions: list[Question]) -> list[DimensionScore]:
    """Calculate per-dimension scores from answered questions.

    Args:
        questions: List of questions with dimension and scores.

    Returns:
        List of DimensionScore objects.
    """
    dim_map: dict[str, dict] = {}

    for q in questions:
        if q.dimension not in dim_map:
            dim_map[q.dimension] = {
                "label": q.dimension_label,
                "total_weight": 0.0,
                "weighted_sum": 0.0,
                "questions": [],
            }
        d = dim_map[q.dimension]
        d["total_weight"] += q.weight
        d["questions"].append(q)
        if q.score is not None:
            d["weighted_sum"] += q.score * q.weight

    results = []
    for key, data in dim_map.items():
        score = round(data["weighted_sum"] / data["total_weight"] * 10, 1) if data["total_weight"] > 0 else 0.0
        results.append(DimensionScore(
            key=key,
            label=data["label"],
            score=score,
            questions=data["questions"],
        ))

    return results


def get_recommendation(score: float) -> str:
    """Generate recommendation text based on score."""
    if score >= 8.0:
        return "高度推荐安装。该 Skill 与你的工作场景高度匹配，安装后可立即投入使用。"
    elif score >= 6.0:
        return "推荐安装，但需注意部分维度可能需要额外配置或调整。建议安装后验证关键场景。"
    elif score >= 4.0:
        return "谨慎安装。该 Skill 在部分维度与你匹配，但在关键环节存在差距。建议先确认差距是否可解决。"
    elif score >= 2.0:
        return "不建议安装。该 Skill 与你的需求匹配度较低，安装后使用频率可能很低。"
    else:
        return "强烈不建议安装。该 Skill 与你的工作场景基本不匹配，安装价值极低。"


def _estimate_dimension_scores(profile: SkillProfile) -> dict[str, float]:
    """Estimate dimension scores (0.0-1.0) from parsed skill content.

    Uses heuristics based on what the parser extracted to give meaningful
    non-interactive scores instead of a flat 0.5.
    """
    scores: dict[str, float] = {}

    # ── use_case (25%) ──
    checks = _check_use_case(profile)
    score = 0.4  # base: neutral-low (we can't know the user's actual needs)
    if checks["has_triggers"]:
        score += 0.25  # skill clearly defines its scope
    if checks["has_summary"]:
        score += 0.15
    if len(profile.triggers) >= 5:
        score += 0.1  # rich trigger vocabulary = broader applicability
    if len(profile.capabilities) >= 3:
        score += 0.1  # multiple capabilities
    scores["use_case"] = min(score, 1.0)

    # ── environment (20%) ──
    checks = _check_environment(profile)
    score = 0.6  # base: assume most environments are capable
    if checks["has_tools"]:
        score -= 0.1  # external tools = potential setup friction
        if len(profile.tools_required) >= 4:
            score -= 0.1  # many tools = higher barrier
    if checks["has_dependencies"]:
        score -= 0.05  # pip dependencies = minor friction
    if not checks["has_tools"] and not checks["has_dependencies"]:
        score += 0.15  # zero external deps = easy to run
    scores["environment"] = max(0.1, min(score, 1.0))

    # ── prerequisites (20%) ──
    checks = _check_prerequisites(profile)
    score = 0.7  # base: most skills are designed to be usable
    if checks["has_requirements"]:
        score -= 0.15  # explicit requirements = potential friction
        if len(profile.requirements) >= 4:
            score -= 0.1  # many requirements
    if checks["has_read_when"]:
        score += 0.1  # well-defined trigger scenarios
    if not checks["has_requirements"]:
        score += 0.1  # no explicit barriers
    scores["prerequisites"] = max(0.1, min(score, 1.0))

    # ── workflow (20%) ──
    checks = _check_workflow(profile)
    score = 0.5  # base: unknown fit
    line_count = len(profile.instructions.split("\n"))
    if checks["has_instructions"]:
        score += 0.15  # substantial instructions = well thought out
    if checks["has_capabilities"]:
        score += 0.15
        if len(profile.capabilities) >= 5:
            score += 0.1  # comprehensive capabilities
    if line_count >= 50:
        score += 0.1  # detailed workflow
    if line_count >= 150:
        score -= 0.05  # overly complex = harder to adopt
    scores["workflow"] = max(0.1, min(score, 1.0))

    # ── documentation (15%) ──
    checks = _check_documentation(profile)
    score = 0.3  # base: assume moderate docs
    section_count = len(profile.all_sections)
    if checks["has_sections"]:
        score += 0.2
    if section_count >= 4:
        score += 0.15  # well-structured
    if section_count >= 7:
        score += 0.1  # very thorough
    if profile.summary and len(profile.summary) >= 50:
        score += 0.1  # good summary
    if profile.description and len(profile.description) >= 100:
        score += 0.1  # good description
    if section_count >= 2 and len(profile.instructions) >= 200:
        score += 0.05  # substantial body
    scores["documentation"] = max(0.1, min(score, 1.0))

    return scores


def analyze(
    skill_path: str,
    use_llm: bool = False,
    llm_config: Optional[LLMConfig] = None,
    num_questions: int = 8,
) -> AnalysisResult:
    """Run full analysis on a SKILL.md file.

    Args:
        skill_path: Path to the SKILL.md file.
        use_llm: Whether to use LLM for question generation.
        llm_config: LLM configuration (required if use_llm=True).
        num_questions: Number of questions to generate.

    Returns:
        Complete AnalysisResult.
    """
    profile = parse_skill(skill_path)

    if use_llm and llm_config and llm_config.enabled:
        questions = generate_questions_llm(profile, llm_config, num_questions)
    else:
        questions = generate_questions_rule_based(profile, num_questions)

    # Estimate scores from content analysis (non-interactive mode)
    dim_estimates = _estimate_dimension_scores(profile)

    # Map question scores from dimension estimates
    for q in questions:
        base_dim_score = dim_estimates.get(q.dimension, 0.5)
        # Add small per-question variance (±0.08) to avoid identical scores
        import random
        variance = (q.id * 7 % 17 - 8) / 100.0  # deterministic: ±0.08
        q.score = max(0.05, min(0.95, base_dim_score + variance))

    overall = calculate_score(questions)
    dim_scores = calculate_dimension_scores(questions)

    return AnalysisResult(
        skill=profile,
        questions=questions,
        dimension_scores=dim_scores,
        overall_score=overall,
        recommendation=get_recommendation(overall),
        details="自动评分模式：基于 Skill 内容特征（触发词、工具依赖、文档结构等）估算适配度。使用 --interactive 模式获取个性化精确评分。",
    )
