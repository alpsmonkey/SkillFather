"""Unit tests for the analyzer module — scoring logic, dimension calculation, recommendations."""

import pytest
from skillfather.analyzer import (
    Question,
    DimensionScore,
    AnalysisResult,
    calculate_score,
    calculate_dimension_scores,
    get_recommendation,
    generate_questions_rule_based,
)
from skillfather.parser import SkillProfile


def _make_profile(**overrides) -> SkillProfile:
    """Create a minimal SkillProfile for testing."""
    defaults = dict(
        path="/test/SKILL.md",
        raw_content="# Test Skill\n\nA test skill for unit tests.",
        name="Test Skill",
        summary="A test skill for unit tests.",
        triggers=["test", "分析"],
        tools_required=["mcp__test"],
        requirements=["Python 3.10+"],
        capabilities=["数据查询", "报表生成"],
        instructions="Step 1: Do something\nStep 2: Done\n" * 10,
    )
    defaults.update(overrides)
    return SkillProfile(**defaults)


def _make_questions(dim_scores: dict[str, list[float]]) -> list[Question]:
    """Create questions with given dimension -> scores mapping."""
    questions = []
    qid = 0
    for dim, scores in dim_scores.items():
        for s in scores:
            qid += 1
            questions.append(Question(
                id=qid,
                text=f"Q{qid}",
                dimension=dim,
                dimension_label=dim,
                explanation="test",
                weight=0.2,
                score=s,
            ))
    return questions


class TestCalculateScore:
    """Test calculate_score with various inputs."""

    def test_empty_questions(self):
        assert calculate_score([]) == 0.0

    def test_all_perfect_scores(self):
        qs = _make_questions({"use_case": [1.0, 1.0]})
        assert calculate_score(qs) == 10.0

    def test_all_zero_scores(self):
        qs = _make_questions({"use_case": [0.0, 0.0]})
        assert calculate_score(qs) == 0.0

    def test_mixed_scores(self):
        qs = _make_questions({"use_case": [1.0], "environment": [0.5]})
        # Equal weights: (1.0 + 0.5) / 2 * 10 = 7.5
        assert calculate_score(qs) == 7.5

    def test_unscored_questions_ignored(self):
        q = Question(id=1, text="Q1", dimension="use_case", dimension_label="use_case",
                     explanation="test", score=None)
        assert calculate_score([q]) == 0.0


class TestCalculateDimensionScores:
    """Test calculate_dimension_scores."""

    def test_single_dimension(self):
        qs = _make_questions({"use_case": [1.0, 0.8]})
        dim_scores = calculate_dimension_scores(qs)
        assert len(dim_scores) == 1
        assert dim_scores[0].key == "use_case"
        assert dim_scores[0].score == 9.0  # (1.0 + 0.8) / 2 * 10

    def test_multiple_dimensions(self):
        qs = _make_questions({"use_case": [1.0], "environment": [0.5]})
        dim_scores = calculate_dimension_scores(qs)
        assert len(dim_scores) == 2
        keys = {ds.key for ds in dim_scores}
        assert "use_case" in keys
        assert "environment" in keys

    def test_empty_questions(self):
        dim_scores = calculate_dimension_scores([])
        assert dim_scores == []


class TestGetRecommendation:
    """Test get_recommendation threshold logic."""

    def test_high_recommendation(self):
        rec = get_recommendation(9.0)
        assert "高度推荐" in rec

    def test_moderate_recommendation(self):
        rec = get_recommendation(7.0)
        assert "推荐" in rec

    def test_cautious_recommendation(self):
        rec = get_recommendation(5.0)
        assert "谨慎" in rec

    def test_not_recommended(self):
        rec = get_recommendation(3.0)
        assert "不建议" in rec

    def test_strong_not_recommended(self):
        rec = get_recommendation(1.0)
        assert "强烈不建议" in rec

    def test_boundary_values(self):
        # Exact thresholds
        assert "高度推荐" in get_recommendation(8.0)
        assert "推荐" in get_recommendation(6.0)
        assert "谨慎" in get_recommendation(4.0)
        assert "不建议" in get_recommendation(2.0)


class TestGenerateQuestionsRuleBased:
    """Test rule-based question generation."""

    def test_generates_questions(self):
        profile = _make_profile()
        questions = generate_questions_rule_based(profile, num_questions=8)
        assert len(questions) >= 5  # At least one per dimension
        assert all(isinstance(q, Question) for q in questions)

    def test_num_questions_limit(self):
        profile = _make_profile()
        questions = generate_questions_rule_based(profile, num_questions=5)
        assert len(questions) <= 5

    def test_questions_cover_dimensions(self):
        profile = _make_profile()
        questions = generate_questions_rule_based(profile, num_questions=10)
        dims = {q.dimension for q in questions}
        # Should cover all 5 dimensions
        expected = {"use_case", "environment", "prerequisites", "workflow", "documentation"}
        assert dims == expected

    def test_question_ids_sequential(self):
        profile = _make_profile()
        questions = generate_questions_rule_based(profile, num_questions=8)
        ids = [q.id for q in questions]
        assert ids == list(range(1, len(questions) + 1))
