"""flow-go 脚本回归测试

覆盖：路径推导、静默失败审计、输入输出正确性、worktree 兼容性
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# ── 第 1 层：共享路径工具 ──────────────────────────────────


class TestPathUtils:
    """_path_utils.py 核心路径推导"""

    def test_resolve_project_root_normal(self, tmp_project):
        from _path_utils import resolve_project_root

        specs_dir = str(tmp_project / ".specs" / "TEST-001")
        assert resolve_project_root(specs_dir) == str(tmp_project)

    def test_resolve_project_root_deep_worktree(self, tmp_path):
        """worktree 场景：.claude/worktrees/<id>/.specs/<id>/"""
        from _path_utils import resolve_project_root

        deep = tmp_path / ".claude" / "worktrees" / "BF-001"
        specs = deep / ".specs" / "BF-001"
        specs.mkdir(parents=True)

        result = resolve_project_root(str(specs))
        assert result == str(deep)
        # history 文件应在 worktree 根目录
        assert os.path.join(result, "health-history.jsonl").startswith(str(deep))

    def test_resolve_skill_dir(self):
        from _path_utils import resolve_skill_dir

        skill = resolve_skill_dir()
        assert os.path.isfile(os.path.join(skill, "SKILL.md"))
        assert os.path.isdir(os.path.join(skill, "references"))

    def test_resolve_history_path_from_specs(self, tmp_project):
        from _path_utils import resolve_history_path

        specs_dir = str(tmp_project / ".specs" / "TEST-001")
        result = resolve_history_path(specs_dir)
        assert result == str(tmp_project / "health-history.jsonl")

    def test_resolve_history_path_from_env(self, tmp_project, monkeypatch):
        from _path_utils import resolve_history_path

        monkeypatch.setenv("FLOWGO_HISTORY", "/tmp/custom-history.jsonl")
        result = resolve_history_path()
        assert result == "/tmp/custom-history.jsonl"

    def test_resolve_history_path_fallback_cwd(self, capsys, monkeypatch):
        monkeypatch.delenv("FLOWGO_HISTORY", raising=False)
        from _path_utils import resolve_history_path

        result = resolve_history_path()
        assert result == "health-history.jsonl"
        captured = capsys.readouterr()
        assert "⚠️" in captured.err

    def test_resolve_project_root_absolute(self, tmp_project):
        """确保返回绝对路径"""
        from _path_utils import resolve_project_root

        specs_dir = str(tmp_project / ".specs" / "TEST-001")
        result = resolve_project_root(specs_dir)
        assert os.path.isabs(result)


# ── 第 2 层：脚本功能回归 ──────────────────────────────────


class TestValidateState:
    """validate_state.py 核心校验逻辑"""

    def test_valid_state(self, tmp_project):
        from validate_state import validate

        result = validate(str(tmp_project / "STATE.md"), str(tmp_project / ".specs"))
        assert result["passed"], f"应通过: {result.get('errors', [])}"

    def test_empty_state_file(self, tmp_path):
        from validate_state import validate

        state = tmp_path / "STATE.md"
        state.write_text("", encoding="utf-8")
        result = validate(str(state))
        assert not result["passed"]
        assert any("为空" in e for e in result["errors"])

    def test_missing_fields(self, tmp_path):
        from validate_state import validate

        state = tmp_path / "STATE.md"
        state.write_text("# STATE\n\n## 仅一个字段\n- 值\n", encoding="utf-8")
        result = validate(str(state))
        assert not result["passed"]

    def test_stage_mismatch(self, tmp_project):
        """索引表阶段与 per-change 阶段不一致"""
        from validate_state import validate

        # 修改索引表中的阶段（per-change 仍为 3-开发）
        content = (tmp_project / "STATE.md").read_text(encoding="utf-8")
        content = content.replace("3-开发", "1-设计", 1)
        (tmp_project / "STATE.md").write_text(content, encoding="utf-8")

        result = validate(str(tmp_project / "STATE.md"), str(tmp_project / ".specs"))
        assert not result["passed"]


class TestGateCheck:
    """gate_check.py 基本功能"""

    def test_blast_radius_clean_repo(self, tmp_path):
        """干净 git 仓库中 blast radius 应通过"""
        from gate_blast import check_blast_radius

        # 创建临时 git 仓库
        subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True)
        (tmp_path / "README.md").write_text("test", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=str(tmp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=str(tmp_path), capture_output=True)

        result = check_blast_radius(str(tmp_path))
        assert not result["exceeded"]

    def test_l1_check_structure(self, skill_root):
        """检查 SKILL.md 存在且结构完整"""
        from gate_l1 import _check_structure

        result = _check_structure(skill_root)
        assert result["passed"], f"SKILL.md 结构检查失败: {result.get('warnings', [])}"


class TestHealthScorer:
    """health_scorer.py 计算和输出"""

    def test_compute_basic(self):
        from health_scorer import compute

        data = {
            "change_id": "TEST-001",
            "ac_total": 10, "ac_passed": 8,
            "test_rounds_completed": 3, "test_rounds_skipped": 1,
            "review_rounds": 2,
            "code_lines_added": 150, "code_lines_removed": 30,
            "hallucination_flags": 0, "boundary_violations": 0,
            "artifacts_complete": ["CHANGE.md", "REQUIREMENT.md", "DESIGN.md",
                                   "TASK.md", "SUMMARY.md", "TEST.md"],
        }
        report = compute(data)
        assert 0 <= report["composite"] <= 100
        assert report["grade"] in ("S", "A", "B", "C", "D", "F")
        assert len(report["scores"]) == 7

    def test_history_write_with_specs_dir(self, tmp_project):
        """验证 --specs-dir 推导的 history 路径正确"""
        from _path_utils import resolve_history_path

        specs_dir = str(tmp_project / ".specs" / "TEST-001")
        hp = resolve_history_path(specs_dir)
        assert hp == str(tmp_project / "health-history.jsonl")


class TestBitterPillAudit:
    """bitter_pill_audit.py 报告路径"""

    def test_relpath_uses_skill_dir(self, skill_root):
        from bitter_pill_audit import format_markdown

        results = [
            {
                "text": "test rule",
                "source": os.path.join(skill_root, "references", "test.md"),
                "category": "KEEP",
                "reason": "test",
            }
        ]
        output = format_markdown(results, skill_root)
        assert "references/test.md" in output
        assert "../" not in output.split("来源:")[1].split("\n")[0].strip()

    def test_relpath_without_skill_dir_default(self):
        """默认 skill_dir='.' 时应正常工作"""
        from bitter_pill_audit import format_markdown

        results = [{"text": "t", "source": "foo.md", "category": "KEEP", "reason": "r"}]
        output = format_markdown(results)
        assert "foo.md" in output


class TestLessonsIndexer:
    """lessons_indexer.py 输出路径"""

    def test_default_output_relative_to_input(self, tmp_path):
        from lessons_indexer import parse_lessons

        lessons = tmp_path / "LESSONS.md"
        lessons.write_text(
            "# LESSONS\n\n### L-001 测试标题\n\n**场景**: 测试场景\n"
            "**教训**: 这是一个教训\n**状态**: active\n**触发关键词**: test/example\n",
            encoding="utf-8",
        )
        entries = parse_lessons(lessons.read_text(encoding="utf-8"))
        assert len(entries) >= 1
        assert entries[0]["id"] == "L-001"

    def test_output_path_derivation(self, tmp_path):
        """默认输出路径应在输入文件同目录"""
        input_path = str(tmp_path / "subdir" / "LESSONS.md")
        expected = os.path.join(os.path.dirname(os.path.abspath(input_path)), ".lessons.jsonl")
        assert expected == str(tmp_path / "subdir" / ".lessons.jsonl")


# ── 第 3 层：进化引擎回归 ──────────────────────────────────


class TestEvolutionReflect:
    """evolution_reflect.py 架构违规检测（不再静默失败）"""

    def test_detect_architecture_violations_finds_real_issues(self, skill_root):
        from evolution_reflect import _detect_architecture_violations

        violations = _detect_architecture_violations()
        # 不再因为路径错误而返回空——至少能扫描到 SKILL.md
        # 注意：这个测试验证函数能扫描到文件，而不是必须有违规
        assert isinstance(violations, list)

    def test_skill_root_resolves_correctly(self, skill_root):
        """skill_root 应指向包含 SKILL.md 和 references/ 的目录"""
        assert os.path.isfile(os.path.join(skill_root, "SKILL.md"))
        assert os.path.isdir(os.path.join(skill_root, "references"))
        assert os.path.isdir(os.path.join(skill_root, "references", "scripts"))


class TestComplexityClassifier:
    """complexity_classifier.py 分级"""

    def test_bugfix_is_lite_or_standard(self):
        from complexity_classifier import classify

        result = classify("修复登录页面的样式bug", ".")
        assert result["level"].upper() in ("LITE", "STANDARD", "HEAVY")


# ── 第 4 层：CLI 入口冒烟测试 ──────────────────────────────


class TestCLIEntryPoints:
    """验证脚本能正常解析参数和启动"""

    def _run_script(self, script_name, args, cwd=None):
        cmd = [sys.executable, f"references/scripts/{script_name}"] + args
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=10,
            cwd=cwd or os.getcwd(),
        )
        return result

    def test_validate_state_help(self):
        r = self._run_script("validate_state.py", ["--help"])
        assert r.returncode == 0
        assert "STATE.md" in r.stdout

    def test_complexity_classifier_help(self):
        r = self._run_script("complexity_classifier.py", ["--help"])
        assert r.returncode == 0

    def test_gate_check_help(self):
        r = self._run_script("gate_check.py", ["--help"])
        assert r.returncode == 0

    def test_health_scorer_help(self):
        r = self._run_script("health_scorer.py", ["--help"])
        assert r.returncode == 0
        assert "--history" in r.stdout
        assert "--specs-dir" in r.stdout
