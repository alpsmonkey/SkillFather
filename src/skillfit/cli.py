"""Command-line interface for SkillFit - Multi-Platform Agent Skill Analyzer."""

import argparse
import sys
from pathlib import Path
from skillfit.parser import parse_skill
from skillfit.analyzer import (
    analyze,
    generate_questions_rule_based,
    generate_questions_llm,
    calculate_score,
    calculate_dimension_scores,
    get_recommendation,
    Question,
    AnalysisResult,
)
from skillfit.reporter import generate_html_report, generate_markdown_report
from skillfit.config import get_llm_config, get_analysis_config
from skillfit.platforms import (
    get_platform,
    list_platforms,
    detect_platform,
    parse_skill_file,
)


def _print_banner(platform: str = None):
    platform_tag = f" - {platform}" if platform else " - Multi-Platform"
    print()
    print("  ╔════════════════════════════════════════════════╗")
    print(f"  ║  SkillFit{platform_tag:<32s}  ║")
    print("  ║  Agent Skill 适配度分析工具 (v0.2.0)         ║")
    print("  ╚════════════════════════════════════════════════╝")
    print()


def _parse_score_input(text: str) -> float:
    """Parse user score input into 0.0-1.0 range."""
    text = text.strip().lower()
    if text in ("y", "yes", "是", "1"):
        return 1.0
    if text in ("n", "no", "否", "0"):
        return 0.0
    if text in ("p", "partial", "部分", "0.5"):
        return 0.5
    try:
        val = float(text)
        return max(0.0, min(1.0, val / 10.0))
    except ValueError:
        return 0.5  # Default


def cmd_analyze(args):
    """Analyze a skill file."""
    skill_path = args.skill_path
    if not Path(skill_path).exists():
        print(f"[ERROR] File not found: {skill_path}")
        return 1

    llm_config = get_llm_config(args.config)
    analysis_config = get_analysis_config(args.config)

    use_llm = args.llm and llm_config.enabled
    num_q = analysis_config.num_questions

    # Determine platform
    platform_name = args.platform
    adapter = None
    if platform_name:
        adapter = get_platform(platform_name)
    else:
        adapter = detect_platform(skill_path)
        if adapter:
            platform_name = adapter.get_platform_name()

    _print_banner(platform_name)

    # Parse skill with platform adapter
    if adapter:
        try:
            profile = adapter.parse(skill_path)
        except Exception as e:
            print(f"  [WARN] Platform parser failed ({e}), falling back to generic parser")
            profile = parse_skill(skill_path)
    else:
        profile = parse_skill(skill_path)

    # Display platform info
    if adapter:
        info = adapter.info()
        print(f"  平台: {info.display_name}")
    print(f"  SKILL: {profile.display_name}")
    print(f"  路径:  {profile.path}")
    print(f"  描述:  {profile.summary[:80] if profile.summary else '无摘要'}")
    print()

    if args.interactive:
        return _run_interactive(profile, use_llm, llm_config, num_q, args)
    else:
        return _run_batch(profile, use_llm, llm_config, num_q, args)


def cmd_list_platforms(args):
    """List supported platforms."""
    print()
    print("  SkillFit 支持的 Agent 平台")
    print("  " + "=" * 50)
    print()

    platforms = list_platforms()
    for p in platforms:
        print(f"  {p.display_name}")
        print(f"    ID:      {p.name}")
        print(f"    格式:    {p.skill_format}")
        print(f"    存储路径: {p.storage_paths[0]}")
        if p.docs_url:
            print(f"    文档:    {p.docs_url}")
        print()

    return 0


def _run_interactive(profile, use_llm, llm_config, num_q, args):
    """Run interactive analysis mode."""
    print("  模式: 交互式问答（请根据你的实际情况回答）\n")
    print("  评分标准：")
    print("    完全满足 → 输入 y/是/10")
    print("    部分满足 → 输入 p/部分/5")
    print("    完全不满足 → 输入 n/否/0")
    print("    也可以直接输入 1-10 的数字\n")

    if use_llm:
        questions = generate_questions_llm(profile, llm_config, num_q)
    else:
        questions = generate_questions_rule_based(profile, num_q)

    dim_labels = {
        "use_case": "用例契合度",
        "environment": "环境就绪度",
        "prerequisites": "前置条件",
        "workflow": "工作流匹配",
        "documentation": "文档质量",
    }

    for q in questions:
        print(f"  -- Q{q.id} [{dim_labels.get(q.dimension, q.dimension_label)}] --")
        print(f"  {q.text}")
        print(f"  -> {q.explanation}")
        print()
        answer = input("  你的回答 [y/p/n/0-10]: ").strip()
        q.answer = answer
        q.score = _parse_score_input(answer)
        print(f"  评分: {q.score * 10:.1f}/10")
        print()

    # Calculate results
    overall = calculate_score(questions)
    dim_scores = calculate_dimension_scores(questions)

    result = AnalysisResult(
        skill=profile,
        questions=questions,
        dimension_scores=dim_scores,
        overall_score=overall,
        recommendation=get_recommendation(overall),
        details="交互模式：基于你的实际回答计算评分。",
    )

    _print_results(result, args)


def _run_batch(profile, use_llm, llm_config, num_q, args):
    """Run batch analysis mode (non-interactive)."""
    print("  模式: 非交互分析（生成诊断问题 + 默认中性评分）\n")

    result = analyze(
        args.skill_path,
        use_llm=use_llm,
        llm_config=llm_config if use_llm else None,
        num_questions=num_q,
    )

    _print_results(result, args)


def _print_results(result: AnalysisResult, args):
    """Print and optionally save analysis results."""
    print()
    print("  ================================================")
    print(f"  综合评分：{result.overall_score:.1f} / 10")
    print(f"  评估结论：{result.recommendation}")
    print(f"  说明：{result.details}")
    print("  ================================================")
    print()

    # Dimension breakdown
    dim_labels = {
        "use_case": "用例契合度",
        "environment": "环境就绪度",
        "prerequisites": "前置条件",
        "workflow": "工作流匹配",
        "documentation": "文档质量",
    }

    for ds in result.dimension_scores:
        label = dim_labels.get(ds.key, ds.label)
        bar_len = 10
        filled = int(ds.score / 10 * bar_len)
        bar = "#" * filled + "-" * (bar_len - filled)
        print(f"  {label:　<8} [{bar}] {ds.score:.1f}/10")

    print()

    # Questions
    print("  -- 诊断问题 --\n")
    for q in result.questions:
        dim_label = dim_labels.get(q.dimension, q.dimension_label)
        score_str = f"{q.score * 10:.1f}/10" if q.score is not None else "未评分"
        print(f"  Q{q.id} [{dim_label}] {q.text}")
        print(f"      评分: {score_str} | {q.explanation[:50]}...")
        print()

    # Save reports
    fmt = args.format or "console"

    if fmt in ("html", "all"):
        out = args.output or f"skillfit_{Path(result.skill.path).stem}.html"
        if not out.endswith(".html"):
            out = out + ".html"
        generate_html_report(result, out)
        print(f"  [OK] HTML 报告已保存: {out}")

    if fmt in ("markdown", "md", "all"):
        base = args.output or f"skillfit_{Path(result.skill.path).stem}"
        out_md = base.replace(".html", "")
        if not out_md.endswith(".md"):
            out_md = out_md + ".md"
        generate_markdown_report(result, out_md)
        print(f"  [OK] Markdown 报告已保存: {out_md}")

    return 0


def main(argv=None):
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="skillfit",
        description="SkillFit - Multi-Platform Agent Skill 适配度分析工具。支持 WorkBuddy、CodeBuddy、Codex、Claude Code、Coze、Hermes Agent。",
    )

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # analyze subcommand
    analyze_parser = subparsers.add_parser("analyze", help="分析一个 Skill 文件")
    analyze_parser.add_argument("skill_path", help="Skill 文件路径 (SKILL.md / .claude/commands/*.md / .skill / .zip / 目录)")
    analyze_parser.add_argument(
        "-p", "--platform",
        choices=["workbuddy", "codebuddy", "codex", "claude-code", "coze", "hermes", "auto"],
        default=None,
        help="指定平台（默认 auto 自动检测）",
    )
    analyze_parser.add_argument(
        "-i", "--interactive", action="store_true",
        help="交互式问答模式（更精确的评分）",
    )
    analyze_parser.add_argument(
        "-f", "--format", choices=["console", "html", "markdown", "md", "all"],
        default="console", help="输出格式（默认：console）",
    )
    analyze_parser.add_argument(
        "-o", "--output", help="输出文件路径",
    )
    analyze_parser.add_argument(
        "--llm", action="store_true",
        help="使用 LLM 生成更精准的问题（需要 API Key）",
    )
    analyze_parser.add_argument(
        "-c", "--config", help="配置文件路径（JSON）",
    )

    # list-platforms subcommand
    subparsers.add_parser("platforms", help="列出所有支持的平台")

    # version
    parser.add_argument("-v", "--version", action="version", version="skillfit 0.2.0")

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "analyze":
        return cmd_analyze(args)
    elif args.command == "platforms":
        return cmd_list_platforms(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
