#!/usr/bin/env python3
"""闸门检查器 — CLI 调度器

瘦入口，按 --mode 分发到子模块：
  --mode l1-guard      → gate_l1.py
  --mode quality-gate  → gate_l2.py [+ gate_l3.py if --enable-l3]
  --mode blast-radius  → gate_blast.py
  --stage N            → gate_artifacts.py

向后兼容：check_artifacts / check_blast_radius / check_quality_gate 仍可导入。
"""
import argparse
import json
import sys

from gate_artifacts import check_artifacts
from gate_blast import check_blast_radius
from gate_l2 import check as _l2_check


def check_quality_gate(stage, specs_dir, project_dir, enable_l3=False, traces_path=None):
    """quality-gate 模式：委托 gate_l2，可选 gate_l3"""
    result = _l2_check(specs_dir, project_dir)

    if enable_l3 and traces_path:
        from gate_l3 import check as _l3_check
        l3 = _l3_check(specs_dir, traces_path)
        result["l3"] = l3
        if not l3["passed"]:
            result["passed"] = False

    return result


def main():
    parser = argparse.ArgumentParser(description="flow-go 闸门检查器")
    parser.add_argument("--stage", type=int, help="目标阶段编号 (0-7)")
    parser.add_argument("--specs-dir", help=".specs/<change-id> 目录路径")
    parser.add_argument("--complexity", choices=["lite", "standard", "heavy"], default="standard")
    parser.add_argument("--mode", choices=["blast-radius", "quality-gate", "l1-guard"],
                        help="运行模式")
    parser.add_argument("--enable-l3", action="store_true",
                        help="启用 L3 跨 Change 回归检查（需配合 --mode quality-gate）")
    parser.add_argument("--traces", help="traces.jsonl 路径（--enable-l3 时使用）")
    parser.add_argument("--project-dir", help="项目根目录")
    parser.add_argument("--threshold", type=int, default=5, help="文件数阈值（默认 5）")
    args = parser.parse_args()

    if args.mode == "l1-guard":
        if not args.specs_dir or not args.project_dir:
            parser.error("l1-guard 模式需要 --specs-dir 和 --project-dir")
        from gate_l1 import check as _l1_check
        result = _l1_check(args.specs_dir, args.project_dir)

    elif args.mode == "blast-radius":
        if not args.project_dir:
            parser.error("blast-radius 模式需要 --project-dir")
        result = check_blast_radius(args.project_dir, args.threshold)

    elif args.mode == "quality-gate":
        if not args.specs_dir or not args.project_dir:
            parser.error("quality-gate 模式需要 --specs-dir 和 --project-dir")
        result = check_quality_gate(
            getattr(args, "stage", 0), args.specs_dir, args.project_dir,
            enable_l3=args.enable_l3, traces_path=args.traces,
        )

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
