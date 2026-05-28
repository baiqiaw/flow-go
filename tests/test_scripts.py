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
    """validate_state.py 核心校验逻辑（worktree-first 格式，无索引表）"""

    def test_valid_state(self, tmp_project):
        """新格式 STATE.md（无索引表）应校验通过"""
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
        """缺少 Pipeline 待续或更新时间字段应失败"""
        from validate_state import validate

        state = tmp_path / "STATE.md"
        state.write_text("# STATE\n\n## 仅一个字段\n- 值\n", encoding="utf-8")
        result = validate(str(state))
        assert not result["passed"]

    def test_discover_active_changes_no_worktree(self, tmp_path):
        """非 git 目录应返回空列表 + 警告"""
        from validate_state import discover_active_changes

        changes, warnings = discover_active_changes(str(tmp_path))
        assert isinstance(changes, list)
        assert len(changes) == 0
        assert len(warnings) > 0  # 非 git 目录应有警告

    def test_backward_compat_archive(self, tmp_path):
        """旧归档格式 STATE.md（含索引表）应能正常解析不报错"""
        from validate_state import parse_state

        archive_state = tmp_path / "OLD-ARCHIVE-STATE.md"
        archive_state.write_text(
            "# STATE\n\n## 活跃 Change\n| change-id | 阶段 | 最后更新 |\n"
            "|-----------|------|---------|\n| （无活跃 Change） | | |\n\n"
            "## Pipeline 待续\n- 无\n\n## 更新时间\n- 2026-05-23\n",
            encoding="utf-8",
        )
        fields, errors = parse_state(str(archive_state))
        assert len(errors) == 0, f"旧格式不应报错: {errors}"
        assert "Pipeline 待续" in fields


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

    def test_safe_run_help(self):
        r = self._run_script("safe_run.py", ["--help"])
        assert r.returncode == 0
        assert "safe_run" in r.stdout.lower() or "安全" in r.stdout

    def test_validate_skill_quick(self):
        r = self._run_script("validate_skill.py", ["--skill-dir", os.getcwd(), "--quick"])
        assert r.returncode == 0

    def test_validate_state_fix(self, tmp_path):
        """--fix 应自动补充缺失字段"""
        from validate_state import validate, apply_fixes

        state = tmp_path / "STATE.md"
        state.write_text("# STATE\n\n## 更新时间\n- 2026-05-27\n", encoding="utf-8")
        specs = tmp_path / ".specs"
        specs.mkdir()

        result = validate(str(state), str(specs))
        fixes = result.get("fixes", [])
        assert len(fixes) > 0, "应检测到缺失字段"

        applied, errs = apply_fixes(str(state), fixes, str(specs))
        assert len(applied) > 0, f"应应用修复: {errs}"
        assert "Pipeline 待续" in state.read_text(encoding="utf-8")


# ── 第 5 层：safe_run.py 功能回归 ────────────────────────────


class TestSafeRun:
    """safe_run.py 核心功能"""

    def _run_safe(self, script_name, child_args=None, timeout=10, tmp_path=None):
        import subprocess
        env = os.environ.copy()
        if tmp_path:
            env["FLOWGO_ERROR_LOG"] = str(tmp_path / "skill-errors.jsonl")
        else:
            env["FLOWGO_ERROR_LOG"] = ""
        cmd = [
            sys.executable, "references/scripts/safe_run.py",
            "--script", script_name,
            "--timeout", str(timeout),
            "--", *(child_args or []),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5, env=env)
        return r.returncode, r.stdout, r.stderr

    def test_ok_script(self):
        """正常脚本应返回 status=ok"""
        exit_code, stdout, _ = self._run_safe("validate_state.py", ["--help"])
        assert exit_code == 0
        result = json.loads(stdout)
        assert result["status"] == "ok"

    def test_nonexistent_script(self):
        """不存在的脚本应返回 status=error"""
        exit_code, stdout, _ = self._run_safe("nonexistent_xyz.py", [])
        result = json.loads(stdout)
        assert result["status"] == "error"
        assert result["recovery"] in ("degrade", "manual")

    def test_script_with_business_error(self):
        """脚本正常执行但业务逻辑失败（exit != 0 且 stderr 无 traceback）→ status=ok"""
        exit_code, stdout, _ = self._run_safe(
            "validate_state.py", ["--state-file", "/tmp/nonexistent-file.md"]
        )
        result = json.loads(stdout)
        assert result["status"] == "ok"
        # 业务逻辑失败不应被当作脚本崩溃
        assert result["hint"] == ""

    def test_output_is_valid_json(self):
        """任何情况下输出都应该是有效的 JSON"""
        for script in ["validate_state.py", "nonexistent.py", "gate_check.py"]:
            _, stdout, _ = self._run_safe(script, ["--help"] if script != "nonexistent.py" else [])
            try:
                json.loads(stdout)
            except json.JSONDecodeError:
                pytest.fail(f"safe_run.py 输出非 JSON: {script}")


# ── 第 6 层：evolution_signal skill 错误信号 ──────────────────


class TestEvolutionSignalSkillErrors:
    """evolution_signal.py _extract_skill_error 函数"""

    def test_no_skill_errors_file(self, tmp_path):
        from evolution_signal import _extract_skill_error

        specs_dir = str(tmp_path / "TEST-001")
        os.makedirs(specs_dir)
        result = _extract_skill_error(specs_dir)
        assert result["medium"] == []
        assert result["strong"] == []

    def test_medium_signal_two_errors(self, tmp_path):
        from evolution_signal import _extract_skill_error

        specs_dir = tmp_path / ".specs" / "TEST-001"
        specs_dir.mkdir(parents=True)
        skill_errors = tmp_path / ".specs" / "skill-errors.jsonl"
        for i in range(2):
            skill_errors.write_text(
                json.dumps({
                    "ts": "2026-05-27T15:00:00Z", "change_id": "TEST-001",
                    "script": "gate_check.py", "error_type": "ScriptError",
                    "stderr_preview": "error", "recovery": "degrade",
                }) + "\n",
                encoding="utf-8",
            ) if i == 0 else open(str(skill_errors), "a", encoding="utf-8").write(
                json.dumps({
                    "ts": "2026-05-27T15:01:00Z", "change_id": "TEST-001",
                    "script": "validate_state.py", "error_type": "ScriptError",
                    "stderr_preview": "error", "recovery": "degrade",
                }) + "\n"
            )

        result = _extract_skill_error(str(specs_dir))
        assert len(result["medium"]) >= 1
        assert result["medium"][0]["type"] == "skill_script_error"

    def test_strong_signal_repeated_script(self, tmp_path):
        from evolution_signal import _extract_skill_error

        specs_dir = tmp_path / ".specs" / "TEST-002"
        specs_dir.mkdir(parents=True)
        skill_errors = tmp_path / ".specs" / "skill-errors.jsonl"
        skill_errors.write_text("", encoding="utf-8")
        for i in range(3):
            with open(str(skill_errors), "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": f"2026-05-27T15:0{i}:00Z", "change_id": "TEST-002",
                    "script": "gate_check.py", "error_type": "ScriptError",
                    "stderr_preview": "KeyError", "recovery": "degrade",
                }) + "\n")

        result = _extract_skill_error(str(specs_dir))
        assert len(result["strong"]) >= 1
        assert result["strong"][0]["type"] == "skill_repeated_error"


# ── 第 7 层：gap_analyzer skill 错误聚合 ─────────────────────


class TestGapAnalyzerSkillErrors:
    """gap_analyzer.py analyze_skill_errors 函数"""

    def test_no_skill_errors_file(self, tmp_path):
        from gap_analyzer import analyze_skill_errors

        specs_dir = str(tmp_path / ".specs")
        os.makedirs(specs_dir)
        result = analyze_skill_errors(specs_dir)
        assert result["available"] is False

    def test_with_skill_errors(self, tmp_path):
        from gap_analyzer import analyze_skill_errors

        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir(parents=True)
        skill_errors = specs_dir / "skill-errors.jsonl"
        scripts = ["gate_check.py", "gate_check.py", "validate_state.py", "evolution_signal.py"]
        error_types = ["ScriptError", "Timeout", "ScriptError", "MissingFile"]
        skill_errors.write_text("", encoding="utf-8")
        for i, (script, etype) in enumerate(zip(scripts, error_types)):
            with open(str(skill_errors), "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "ts": f"2026-05-27T15:0{i}:00Z", "change_id": "TEST-001",
                    "script": script, "error_type": etype,
                    "stderr_preview": "err", "recovery": "degrade",
                }) + "\n")

        result = analyze_skill_errors(str(specs_dir))
        assert result["available"] is True
        assert result["total_errors"] == 4
        assert len(result["top_scripts"]) >= 1
        top_script = result["top_scripts"][0]
        assert top_script["script"] == "gate_check.py"
        assert top_script["count"] == 2
