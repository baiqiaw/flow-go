#!/usr/bin/env python3
"""闸门检查器 — CLI 调度器

瘦入口，按 --mode 分发到子模块：
  --mode l1-guard      → gate_l1.py
  --mode quality-gate  → gate_l2.py [+ gate_l3.py if --enable-l3]
  --mode blast-radius  → gate_blast.py
  --stage N            → gate_artifacts.py

两层结构支持：
  --change-id 必需参数，指定当前 change-id。
  闸门校验从 .specs/<change-id>/STATE.md 读取当前阶段，
  不再从项目级 STATE.md 读取。

向后兼容：check_artifacts / check_blast_radius / check_quality_gate 仍可导入。
"""
import argparse
import json
import os
import re
import sys

from gate_artifacts import check_artifacts
from gate_blast import check_blast_radius
from gate_l2 import check as _l2_check


def read_stage_from_change_state(specs_dir, change_id):
    """从 .specs/<change-id>/STATE.md 读取当前阶段

    两层结构下，闸门检查所需的「当前阶段」存储在 per-change STATE.md 中，
    而非项目级 STATE.md 的索引表。
    返回阶段字符串（如 "3-开发"），未找到时返回 None。
    """
    change_state_path = os.path.join(specs_dir, change_id, "STATE.md")
    if not os.path.isfile(change_state_path):
        return None
    try:
        with open(change_state_path, encoding="utf-8") as f:
            current_key = None
            for line in f:
                line = line.rstrip("\n")
                m = re.match(r"^##\s+(.+)$", line)
                if m:
                    current_key = m.group(1).strip()
                    continue
                if current_key == "当前阶段" and line.startswith("- "):
                    return line[2:].strip()
    except (OSError, UnicodeDecodeError):
        pass
    return None


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


def _check_adr_context(result: dict, stage: int, complexity: str, specs_dir: str) -> None:
    """ADR/CONTEXT 可选附加检查（不阻塞 passed，仅作为 info/warning 报告）

    规则：
      - stage >= 1 且 complexity == "heavy" → 检查 .specs/adr/ 目录是否存在
      - stage >= 0 且 complexity != "lite"   → 检查 .specs/CONTEXT.md 是否存在
    """
    adr_reported = False
    context_reported = False

    # ADR 目录检查：stage >= 1 且 heavy
    if stage >= 1 and complexity == "heavy":
        # adr 目录相对于 specs_dir 的上一级（.specs/adr/）
        specs_parent = os.path.dirname(specs_dir)
        adr_dir = os.path.join(specs_parent, "adr")
        adr_exists = os.path.isdir(adr_dir)
        result["adr_dir_exists"] = adr_exists
        result.setdefault("info", []).append(
            f"ADR 目录 .specs/adr/ {'存在' if adr_exists else '不存在'}（heavy 模式，仅供参考）"
        )
        adr_reported = True

    # CONTEXT.md 检查：stage >= 0 且非 lite
    if stage >= 0 and complexity != "lite":
        specs_parent = os.path.dirname(specs_dir)
        context_path = os.path.join(specs_parent, "CONTEXT.md")
        context_exists = os.path.isfile(context_path)
        result["context_exists"] = context_exists
        if not context_exists:
            result.setdefault("warnings", []).append(
                "CONTEXT.md 不存在（非 lite 模式建议创建，不阻塞闸门）"
            )
        else:
            result.setdefault("info", []).append(
                "CONTEXT.md 存在"
            )
        context_reported = True

    # 确保即使两种检查都不触发，输出结构也一致
    if not adr_reported:
        result["adr_dir_exists"] = None
    if not context_reported:
        result["context_exists"] = None
    if "info" not in result:
        result["info"] = []


def main():
    parser = argparse.ArgumentParser(description="flow-go 闸门检查器")
    parser.add_argument("--stage", type=int, help="目标阶段编号 (0-7)")
    # --change-id 必需参数：指定当前 change-id，用于从 .specs/<id>/STATE.md 读取当前阶段
    parser.add_argument("--change-id", required=True,
                        help="当前 change-id（必需），用于从 .specs/<id>/STATE.md 读取当前阶段")
    parser.add_argument("--specs-dir", help=".specs/<change-id> 目录路径")
    parser.add_argument("--complexity", type=lambda s: s.lower(),
                        choices=["lite", "standard", "heavy"], default="standard",
                        help="复杂度等级 (lite/standard/heavy，不区分大小写)")
    parser.add_argument("--mode", choices=["blast-radius", "quality-gate", "l1-guard"],
                        help="运行模式")
    parser.add_argument("--enable-l3", action="store_true",
                        help="启用 L3 跨 Change 回归检查（需配合 --mode quality-gate）")
    parser.add_argument("--traces", help="traces.jsonl 路径（--enable-l3 时使用）")
    parser.add_argument("--project-dir", help="项目根目录")
    parser.add_argument("--threshold", type=int, default=5, help="文件数阈值（默认 5）")
    args = parser.parse_args()
    # --complexity 通过 type=lambda s: s.lower() 已自动转为小写

    # 根据参数推导 specs_dir（如果未直接指定）
    specs_dir = args.specs_dir
    if not specs_dir and args.project_dir and args.change_id:
        specs_dir = os.path.join(args.project_dir, ".specs", args.change_id)

    if args.mode == "l1-guard":
        if not specs_dir or not args.project_dir:
            parser.error("l1-guard 模式需要 --specs-dir（或 --project-dir + --change-id）和 --project-dir")
        from gate_l1 import check as _l1_check
        result = _l1_check(specs_dir, args.project_dir)

    elif args.mode == "blast-radius":
        if not args.project_dir:
            parser.error("blast-radius 模式需要 --project-dir")
        result = check_blast_radius(args.project_dir, args.threshold)

    elif args.mode == "quality-gate":
        if not specs_dir or not args.project_dir:
            parser.error("quality-gate 模式需要 --specs-dir（或 --project-dir + --change-id）和 --project-dir")
        stage_val = args.stage if args.stage is not None else 0
        result = check_quality_gate(
            stage_val, specs_dir, args.project_dir,
            enable_l3=args.enable_l3, traces_path=args.traces,
        )

    else:
        # 工件检查模式：优先使用 per-change STATE.md 读取当前阶段
        if args.stage is None:
            # 尝试从 .specs/<change-id>/STATE.md 自动获取当前阶段
            if args.project_dir and args.change_id:
                _base_specs = os.path.join(args.project_dir, ".specs")
                auto_stage = read_stage_from_change_state(_base_specs, args.change_id)
                if auto_stage:
                    # 从阶段字符串提取数字（如 "3-开发" -> 3）
                    try:
                        args.stage = int(auto_stage.split("-")[0])
                    except (ValueError, IndexError):
                        parser.error(f"无法从 per-change STATE.md 的当前阶段 '{auto_stage}' 解析阶段编号")
                else:
                    parser.error("工件检查模式需要 --stage，且 .specs/<change-id>/STATE.md 中未找到当前阶段")
            else:
                parser.error("工件检查模式需要 --stage")
        if not specs_dir:
            parser.error("工件检查模式需要 --specs-dir（或 --project-dir + --change-id）")
        result = check_artifacts(args.stage, specs_dir, args.complexity)

        # 可选的 ADR/CONTEXT 附加检查（不阻塞 passed，仅作为 info/warning 报告）
        _check_adr_context(result, args.stage, args.complexity, args.specs_dir)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("passed", result.get("file_count", 0) <= args.threshold) else 1)


if __name__ == "__main__":
    main()
