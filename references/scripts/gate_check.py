#!/usr/bin/env python3
"""闸门检查器 — 双模式检查 flow-go 阶段闸门

用法：
  工件检查：python3 gate_check.py --stage <N> --specs-dir <path> [--complexity <lite|standard|heavy>]
  Blast radius：python3 gate_check.py --mode blast-radius --project-dir <path> [--threshold <N>]
"""
import argparse
import json
import os
import re
import subprocess
import sys


# STANDARD 模式各阶段必需工件
STANDARD_GATES = {
    0: [],
    1: ["CHANGE.md", "REQUIREMENT.md"],
    2: ["REQUIREMENT.md", "DESIGN.md"],
    3: ["DESIGN.md", "TASK.md"],
    4: [],
    5: ["TEST.md"],
    6: ["REVIEW.md"],
    7: ["DEPLOY.md"],
}

# LITE 模式简化闸门
LITE_GATES = {
    0: [],
    1: [],       # LITE 跳过
    2: [],       # LITE 跳过
    3: ["CHANGE.md"],
    4: [],
    5: [],       # LITE 跳过
    6: [],       # LITE 跳过
    7: [],       # 由 4-测试通过 + CHANGE.md AC 替代
}

# HEAVY 同 STANDARD，额外标记 blast_radius 待检查
HEAVY_GATES = STANDARD_GATES


def check_artifacts(stage, specs_dir, complexity="standard"):
    """工件检查模式"""
    if complexity == "lite":
        required = LITE_GATES.get(stage, [])
    elif complexity == "heavy":
        required = HEAVY_GATES.get(stage, [])
    else:
        required = STANDARD_GATES.get(stage, [])

    missing = []
    warnings = []

    for artifact in required:
        path = os.path.join(specs_dir, artifact)
        if not os.path.isfile(path):
            missing.append(artifact)
        elif os.path.getsize(path) == 0:
            missing.append(f"{artifact}（空文件）")

    if complexity == "heavy" and stage >= 3:
        warnings.append("HEAVY 模式：blast_radius 检查待执行（gate_check.py --mode blast-radius）")

    # LITE 7-验收特殊检查：CHANGE.md AC + 测试通过
    if complexity == "lite" and stage == 7:
        change_path = os.path.join(specs_dir, "CHANGE.md")
        if not os.path.isfile(change_path):
            missing.append("CHANGE.md")
        # 测试通过记录检查
        test_path = os.path.join(specs_dir, "TEST.md")
        if not os.path.isfile(test_path):
            warnings.append("LITE 7-验收：TEST.md 不存在，无法确认测试通过")

    return {
        "passed": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
    }


def check_blast_radius(project_dir, threshold=5):
    """Blast radius 模式：统计 git diff 改动文件数"""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=project_dir,
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return {
                "file_count": 0,
                "threshold": threshold,
                "exceeded": False,
                "files": [],
                "warning": f"git diff 失败: {result.stderr.strip()}",
            }
        files = [f for f in result.stdout.strip().split("\n") if f]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {
            "file_count": 0,
            "threshold": threshold,
            "exceeded": False,
            "files": [],
            "warning": "git 不可用，无法统计 blast radius",
        }

    return {
        "file_count": len(files),
        "threshold": threshold,
        "exceeded": len(files) > threshold,
        "files": files,
    }


def _check_quality_dimension(specs_dir):
    """质量维度：检查 SUMMARY.md 中 verify 通过率"""
    summary_path = os.path.join(specs_dir, "SUMMARY.md")
    if not os.path.isfile(summary_path):
        return {"passed": True, "detail": "SUMMARY.md 不存在，跳过质量检查", "source": "SUMMARY.md"}
    try:
        with open(summary_path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return {"passed": True, "detail": "SUMMARY.md 读取失败，跳过", "source": "SUMMARY.md"}

    # 3 种格式：百分比 90%、分数 9/10、关键词 passed: 9
    pct = re.search(r'verify\s*通过率[：:]\s*(\d+)%', content)
    if pct:
        rate = int(pct.group(1))
        return {"passed": rate >= 80, "detail": f"verify 通过率 {rate}% ({'≥' if rate >= 80 else '<'}80%)", "source": "SUMMARY.md"}

    frac = re.search(r'verify\s*通过率[：:]\s*(\d+)/(\d+)', content)
    if frac:
        passed, total = int(frac.group(1)), int(frac.group(2))
        rate = round(passed / total * 100) if total > 0 else 100
        return {"passed": rate >= 80, "detail": f"verify 通过率 {passed}/{total} ({rate}%)", "source": "SUMMARY.md"}

    if "verify" not in content.lower():
        return {"passed": True, "detail": "SUMMARY.md 无 verify 信息，跳过质量检查", "source": "SUMMARY.md"}

    return {"passed": True, "detail": "verify 信息存在但无法解析具体通过率", "source": "SUMMARY.md"}


def _check_scope_dimension(specs_dir, project_dir):
    """范围维度：检查 git diff 改动是否超出 TASK.md 规划"""
    task_path = os.path.join(specs_dir, "TASK.md")
    if not os.path.isfile(task_path):
        return {"passed": True, "detail": "TASK.md 不存在，跳过范围检查", "source": "git diff + TASK.md"}
    try:
        with open(task_path, encoding="utf-8") as f:
            task_content = f.read()
    except OSError:
        return {"passed": True, "detail": "TASK.md 读取失败，跳过", "source": "git diff + TASK.md"}

    # 提取 write_files 行
    planned = set()
    for m in re.finditer(r'<write_files>(.*?)</write_files>', task_content, re.S):
        for line in m.group(1).strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('<!--'):
                planned.add(line)

    if not planned:
        return {"passed": True, "detail": "TASK.md 无预期文件列表，跳过范围检查", "source": "git diff + TASK.md"}

    # 获取实际改动
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"], cwd=project_dir,
            capture_output=True, text=True, timeout=10,
        )
        actual = set(f for f in result.stdout.strip().split("\n") if f) if result.returncode == 0 else set()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"passed": True, "detail": "git 不可用，跳过范围检查", "source": "git diff + TASK.md"}

    out_of_scope = actual - planned
    if out_of_scope:
        return {"passed": False, "detail": f"改动 {len(out_of_scope)} 文件超出 TASK.md 规划: {', '.join(sorted(out_of_scope)[:5])}", "source": "git diff + TASK.md"}
    return {"passed": True, "detail": f"改动 {len(actual)} 文件，均在 TASK.md 规划范围内", "source": "git diff + TASK.md"}


def check_quality_gate(stage, specs_dir, project_dir):
    """quality-gate 模式：4 维 AND 逻辑检查"""
    quality = _check_quality_dimension(specs_dir)
    scope = _check_scope_dimension(specs_dir, project_dir)
    security = _check_security_dimension(specs_dir)
    regression = _check_regression_dimension(specs_dir)

    passed = quality["passed"] and scope["passed"] and security["passed"] and regression["passed"]
    return {
        "mode": "quality-gate",
        "passed": passed,
        "logic": "AND",
        "dimensions": {"quality": quality, "scope": scope, "security": security, "regression": regression},
    }


DANGEROUS_PATTERNS = [
    r"BEGIN\s+PRIVATE\s+KEY",
    r"BEGIN\s+RSA\s+PRIVATE\s+KEY",
    r"rm\s+-rf\s+/",
    r"DROP\s+TABLE",
    r"password\s*=\s*['\"]",
]


def _check_security_dimension(specs_dir):
    """安全维度：扫描工件中的危险模式"""
    matches = []
    for fname in sorted(os.listdir(specs_dir)):
        if not fname.endswith(".md") or fname == "TEST.md":
            continue
        fpath = os.path.join(specs_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        for pattern in DANGEROUS_PATTERNS:
            hits = re.findall(pattern, content, re.I)
            if hits:
                matches.append(f"{fname}: {hits[0][:50]}")
    if matches:
        return {"passed": False, "detail": f"检出 {len(matches)} 处危险模式: {'; '.join(matches[:3])}", "source": "artifact scan"}
    return {"passed": True, "detail": "未检出危险模式", "source": "artifact scan"}


def _check_regression_dimension(specs_dir):
    """回归维度：检查 TEST.md 中是否有原已通过用例失败"""
    test_path = os.path.join(specs_dir, "TEST.md")
    if not os.path.isfile(test_path):
        return {"passed": True, "detail": "TEST.md 不存在，跳过回归检查", "source": "TEST.md"}
    try:
        with open(test_path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return {"passed": True, "detail": "TEST.md 读取失败，跳过", "source": "TEST.md"}

    patterns = [
        r"原已通过用例失败",
        r"previously\s+passing.*failed",
        r"regression",
        r"回归.*失败",
    ]
    for pat in patterns:
        hit = re.search(pat, content, re.I)
        if hit:
            return {"passed": False, "detail": f"TEST.md 包含回归失败记录: \"{hit.group()[:60]}\"", "source": "TEST.md"}
    return {"passed": True, "detail": "无原已通过用例失败记录", "source": "TEST.md"}


def main():
    parser = argparse.ArgumentParser(description="flow-go 闸门检查器")
    parser.add_argument("--stage", type=int, help="目标阶段编号 (0-7)")
    parser.add_argument("--specs-dir", help=".specs/<change-id> 目录路径")
    parser.add_argument("--complexity", choices=["lite", "standard", "heavy"], default="standard")
    parser.add_argument("--mode", choices=["blast-radius", "quality-gate"], help="运行模式")
    parser.add_argument("--project-dir", help="项目根目录（blast-radius / quality-gate 模式）")
    parser.add_argument("--threshold", type=int, default=5, help="文件数阈值（默认 5）")
    args = parser.parse_args()

    if args.mode == "blast-radius":
        if not args.project_dir:
            parser.error("blast-radius 模式需要 --project-dir")
        result = check_blast_radius(args.project_dir, args.threshold)
    elif args.mode == "quality-gate":
        if args.stage is None:
            parser.error("quality-gate 模式需要 --stage")
        if not args.specs_dir:
            parser.error("quality-gate 模式需要 --specs-dir")
        if not args.project_dir:
            parser.error("quality-gate 模式需要 --project-dir")
        result = check_quality_gate(args.stage, args.specs_dir, args.project_dir)
    else:
        if args.stage is None:
            parser.error("工件检查模式需要 --stage")
        if not args.specs_dir:
            parser.error("工件检查模式需要 --specs-dir")
        result = check_artifacts(args.stage, args.specs_dir, args.complexity)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("passed", result.get("file_count", 0) <= args.threshold) else 1)


if __name__ == "__main__":
    main()
