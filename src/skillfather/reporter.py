"""Report generation - produces HTML and Markdown analysis reports."""

import json
import html as html_module
from pathlib import Path
from datetime import datetime
from skillfather.analyzer import AnalysisResult, DimensionScore


def _get_template_dir() -> Path:
    """Resolve templates directory using importlib.resources (pip-install safe)."""
    try:
        import importlib.resources as pkg_resources
        # Python 3.10+: as_file + files
        ref = pkg_resources.files("skillfather").joinpath("../templates")
        # Resolve to a real path for Path-based operations
        with pkg_resources.as_file(ref) as p:
            return p
    except (ImportError, TypeError, FileNotFoundError):
        pass
    # Fallback: relative path for editable / source installs
    return Path(__file__).parent.parent.parent / "templates"


_TEMPLATE_DIR = _get_template_dir()


def generate_html_report(result: AnalysisResult, output_path: str | Path | None = None) -> str:
    """Generate an HTML report from analysis results.

    Args:
        result: Complete analysis result.
        output_path: If provided, write HTML to this file. Always returns HTML string.

    Returns:
        HTML string of the report.
    """
    template_path = _TEMPLATE_DIR / "report.html"
    if not template_path.exists():
        # Fallback: generate inline HTML
        html = _generate_inline_html(result)
    else:
        template = template_path.read_text(encoding="utf-8")
        html = _render_template(template, result)

    if output_path:
        Path(output_path).write_text(html, encoding="utf-8")

    return html


def generate_markdown_report(result: AnalysisResult, output_path: str | Path | None = None) -> str:
    """Generate a Markdown report from analysis results.

    Args:
        result: Complete analysis result.
        output_path: If provided, write Markdown to this file.

    Returns:
        Markdown string.
    """
    lines = []
    lines.append(f"# {result.skill.display_name} - SKILL 适配度分析报告\n")
    lines.append(f"> 分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    lines.append(f"> 文件路径：{result.skill.path}\n")

    # Score overview
    lines.append("\n---\n")
    lines.append(f"## 综合评分：{result.overall_score:.1f} / 10\n")

    score_bar_len = 20
    filled = int(result.overall_score / 10 * score_bar_len)
    bar = "[" + "#" * filled + "-" * (score_bar_len - filled) + "]"
    lines.append(f"\n{bar} {result.overall_score:.1f}/10\n")

    lines.append(f"\n**评估结论：** {result.recommendation}\n")

    if result.details:
        lines.append(f"\n> {result.details}\n")

    # Dimension scores
    lines.append("\n---\n")
    lines.append("## 维度评分\n")
    lines.append("| 维度 | 评分 | 说明 |")
    lines.append("|------|------|------|")

    for ds in result.dimension_scores:
        label = _DIM_LABELS.get(ds.key, ds.label)
        lines.append(f"| {label} | {ds.score:.1f}/10 | 共 {len(ds.questions)} 个诊断项 |")

    # Questions
    lines.append("\n---\n")
    lines.append("## 诊断问题清单\n")

    for q in result.questions:
        dim_label = _DIM_LABELS.get(q.dimension, q.dimension_label)
        lines.append(f"\n### Q{q.id}. {q.text}\n")
        lines.append(f"- **维度**：{dim_label}")
        lines.append(f"- **评分权重**：{q.weight:.0%}")
        lines.append(f"- **为什么问这个**：{q.explanation}")
        if q.score is not None:
            lines.append(f"- **评分**：{q.score * 10:.1f}/10")

    # Skill metadata
    lines.append("\n---\n")
    lines.append("## SKILL 元信息\n")
    lines.append(f"- **名称**：{result.skill.display_name}")
    lines.append(f"- **描述**：{result.skill.summary or '无'}")
    lines.append(f"- **触发词**：{result.skill.trigger_text}")
    lines.append(f"- **前置条件**：{result.skill.requirement_text}")
    lines.append(f"- **工具依赖**：{result.skill.tool_text}")
    lines.append(f"- **文档章节**：{len(result.skill.all_sections)} 个")
    lines.append(f"- **指令行数**：{len(result.skill.instructions.split(chr(10)))}")

    md = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(md, encoding="utf-8")

    return md


def _get_score_color(score: float) -> str:
    """Return hex color for a given overall score."""
    if score >= 8:
        return "#10B981"
    elif score >= 6:
        return "#3B82F6"
    elif score >= 4:
        return "#F59E0B"
    else:
        return "#EF4444"


def _get_dim_color(dim_key: str) -> str:
    """Return hex color for a dimension key."""
    return {
        "use_case": "#3B82F6",
        "environment": "#10B981",
        "prerequisites": "#F59E0B",
        "workflow": "#8B5CF6",
        "documentation": "#EF4444",
    }.get(dim_key, "#6B7280")


_DIM_LABELS = {
    "use_case": "用例契合度",
    "environment": "环境就绪度",
    "prerequisites": "前置条件",
    "workflow": "工作流匹配",
    "documentation": "文档质量",
}


def _escape_html(text: str) -> str:
    """Escape user-provided text for safe HTML insertion."""
    if not text:
        return ""
    return html_module.escape(str(text), quote=True)


def _render_template(template: str, result: AnalysisResult) -> str:
    """Render HTML template with analysis data."""
    # Build dimension data
    dim_data = []
    for ds in result.dimension_scores:
        label = _DIM_LABELS.get(ds.key, ds.label)
        color = _get_dim_color(ds.key)
        dim_data.append({
            "key": ds.key,
            "label": label,
            "score": ds.score,
            "color": color,
            "question_count": len(ds.questions),
        })

    # Build questions data
    questions_json = json.dumps([
        {
            "id": q.id,
            "text": q.text,
            "dimension": _DIM_LABELS.get(q.dimension, q.dimension_label),
            "dimension_key": q.dimension,
            "explanation": q.explanation,
            "weight": f"{q.weight:.0%}",
            "score": q.score,
        }
        for q in result.questions
    ], ensure_ascii=False, indent=2)

    # Skill metadata
    skill = result.skill
    skill_meta = json.dumps({
        "name": skill.display_name,
        "summary": skill.summary or "",
        "triggers": skill.trigger_text,
        "requirements": skill.requirement_text,
        "tools": skill.tool_text,
        "capabilities": skill.capability_text,
        "section_count": len(skill.all_sections),
        "line_count": len(skill.instructions.split("\n")),
        "path": skill.path,
    }, ensure_ascii=False, indent=2)

    # Score color
    score_color = _get_score_color(result.overall_score)
    score = result.overall_score

    # Escape user-provided strings before HTML insertion
    html = template.replace("{{SCHEDULED_TIME}}", _escape_html(datetime.now().strftime("%Y-%m-%d %H:%M")))
    html = html.replace("{{SKILL_NAME}}", _escape_html(skill.display_name))
    html = html.replace("{{SKILL_PATH}}", _escape_html(skill.path))
    html = html.replace("{{OVERALL_SCORE}}", f"{score:.1f}")
    html = html.replace("{{SCORE_COLOR}}", score_color)
    html = html.replace("{{SCORE_FILL_PCT}}", f"{score * 10:.0f}")
    html = html.replace("{{RECOMMENDATION}}", _escape_html(result.recommendation))
    html = html.replace("{{DETAILS}}", _escape_html(result.details))
    html = html.replace("{{DIMENSION_DATA}}", json.dumps(dim_data, ensure_ascii=False))
    html = html.replace("{{QUESTIONS_DATA}}", questions_json)
    html = html.replace("{{SKILL_META}}", skill_meta)

    return html


def _generate_inline_html(result: AnalysisResult) -> str:
    """Fallback inline HTML generator when template is not available."""
    score_color = _get_score_color(result.overall_score)
    question_cards = ""
    for q in result.questions:
        dim_color = _get_dim_color(q.dimension)
        question_cards += (
            f'<div class="question" style="border-left-color:{dim_color}">'
            f'<h3>Q{_escape_html(str(q.id))}. {_escape_html(q.text)}</h3>'
            f"<p><em>{_escape_html(_DIM_LABELS.get(q.dimension, q.dimension_label))}</em> | {_escape_html(q.explanation)}</p>"
            f"</div>\n"
        )
    safe_name = _escape_html(result.skill.display_name)
    safe_rec = _escape_html(result.recommendation)
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{safe_name} - SkillFather Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 800px; margin: 0 auto; padding: 2rem; color: #333; }}
.score {{ font-size: 4rem; font-weight: bold; color: {score_color}; text-align: center; }}
.question {{ margin: 1.5rem 0; padding: 1rem; border-left: 4px solid {score_color}; background: #f8fafc; }}
</style>
</head>
<body>
<h1>{safe_name} - 适配度分析</h1>
<div class="score">{result.overall_score:.1f}/10</div>
<p>{safe_rec}</p>
{question_cards}
</body>
</html>"""
