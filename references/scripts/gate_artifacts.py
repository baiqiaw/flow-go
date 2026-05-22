#!/usr/bin/env python3
"""工件检查 — 各阶段必需工件验证

从 gate_check.py 提取的 check_artifacts() 及其常量。
"""
import os


# STANDARD 模式各阶段必需工件
STANDARD_GATES = {
    0: ["CHANGE.md"],
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
        test_path = os.path.join(specs_dir, "TEST.md")
        if not os.path.isfile(test_path):
            warnings.append("LITE 7-验收：TEST.md 不存在，无法确认测试通过")

    return {
        "passed": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
        "info": [],
    }
