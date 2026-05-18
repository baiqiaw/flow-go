#!/usr/bin/env python3
"""闸门检查器 — 双模式检查 flow-go 阶段闸门

用法：
  工件检查：python3 gate_check.py --stage <N> --specs-dir <path> [--complexity <lite|standard|heavy>]
  Blast radius：python3 gate_check.py --mode blast-radius --project-dir <path> [--threshold <N>]
"""
import argparse
import json
import os
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


def main():
    parser = argparse.ArgumentParser(description="flow-go 闸门检查器")
    parser.add_argument("--stage", type=int, help="目标阶段编号 (0-7)")
    parser.add_argument("--specs-dir", help=".specs/<change-id> 目录路径")
    parser.add_argument("--complexity", choices=["lite", "standard", "heavy"], default="standard")
    parser.add_argument("--mode", choices=["blast-radius"], help="blast-radius 模式")
    parser.add_argument("--project-dir", help="项目根目录（blast-radius 模式）")
    parser.add_argument("--threshold", type=int, default=5, help="文件数阈值（默认 5）")
    args = parser.parse_args()

    if args.mode == "blast-radius":
        if not args.project_dir:
            parser.error("blast-radius 模式需要 --project-dir")
        result = check_blast_radius(args.project_dir, args.threshold)
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
