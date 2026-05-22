#!/usr/bin/env python3
"""STATE.md 完整性校验器 — 自动化校验，减少模型判断负担

用法：python3 validate_state.py --state-file <path> [--specs-dir <path>]

校验规则来自 meta-artifacts.md「完整性校验」清单。
输出 JSON 格式的校验结果，供 flow-go 第一步读取。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

REQUIRED_FIELDS = [
    "活跃 Change",
    "当前阶段",
    "当前任务",
    "中断任务",
    "Pipeline 待续",
    "并行 Change",
    "更新时间",
]

VALID_STAGES = [
    "0-需求", "1-设计", "2-任务", "3-开发",
    "4-测试", "5-审查", "6-部署", "7-验收",
]

def parse_state(state_path):
    """解析 STATE.md 为字段字典"""
    fields = {}
    current_key = None
    try:
        with open(state_path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                # 匹配 ## 标题行
                m = re.match(r"^##\s+(.+)$", line)
                if m:
                    current_key = m.group(1).strip()
                    continue
                # 匹配列表值
                if current_key and line.startswith("- "):
                    val = line[2:].strip()
                    if current_key not in fields:
                        fields[current_key] = val
                    else:
                        # 多值字段用逗号拼接
                        fields[current_key] += "," + val
    except (OSError, UnicodeDecodeError) as e:
        return None, [f"无法读取文件：{e}"]
    return fields, []


def validate(state_path, specs_dir=None):
    """执行完整性校验，返回结果字典"""
    missing = []
    warnings = []
    info = []

    # 校验 1: 文件存在且非空
    if not os.path.isfile(state_path):
        return {"passed": False, "missing": ["STATE.md 文件不存在"],
                "warnings": [], "info": [], "fields": {}, "fixes": []}

    with open(state_path, encoding="utf-8") as f:
        content = f.read()
    if not content.strip():
        return {"passed": False, "missing": ["STATE.md 文件为空"],
                "warnings": [], "info": [], "fields": {}, "fixes": []}

    # 校验 2: 首行包含 STATE
    first_line = content.split("\n")[0]
    if "STATE" not in first_line:
        missing.append(f"首行不包含 'STATE'：{first_line}")

    # 解析字段
    fields, parse_errors = parse_state(state_path)
    if parse_errors:
        return {"passed": False, "missing": parse_errors,
                "warnings": [], "info": [], "fields": {}, "fixes": []}

    # 校验 3: 7 个字段全部存在
    field_missing = [f for f in REQUIRED_FIELDS if f not in fields]
    if field_missing:
        missing.append(f"缺少必填字段：{', '.join(field_missing)}")

    fixes = []

    # 校验 4: 活跃 Change 非空时目录存在
    active = fields.get("活跃 Change", "")
    if active and active != "无" and specs_dir:
        # 路径遍历防护：change-id 应为合法 kebab-case，不含路径分隔符
        if ".." in active or "/" in active or "\\" in active:
            missing.append(f"活跃 Change '{active}' 包含非法路径字符")
        else:
            change_dir = os.path.join(specs_dir, active)
            if not os.path.isdir(change_dir):
                missing.append(f"活跃 Change '{active}' 对应的 .specs/{active}/ 目录不存在")

    # 校验 5: 当前阶段合法
    stage = fields.get("当前阶段", "")
    if stage and stage != "无" and stage not in VALID_STAGES:
        missing.append(f"当前阶段 '{stage}' 不在合法值中：{VALID_STAGES}")

    # 校验 6: 中断任务和当前任务不重复
    cur_task = fields.get("当前任务", "")
    int_task = fields.get("中断任务", "")
    if cur_task and int_task and cur_task != "无" and int_task != "无" and cur_task == int_task:
        missing.append(f"当前任务和中断任务相同：{cur_task}")

    # 校验 7: Pipeline 待续验证（宽松）
    pipeline = fields.get("Pipeline 待续", "")
    if pipeline and pipeline != "无":
        warnings.append(f"Pipeline 待续非空：{pipeline}，请确认对应 change-id 存在")

    # 校验 8: 更新时间格式
    update_time = fields.get("更新时间", "")
    if update_time and update_time != "无":
        try:
            datetime.strptime(update_time, "%Y-%m-%d")
        except ValueError:
            missing.append(f"更新时间格式不正确：'{update_time}'，应为 YYYY-MM-DD")

    # 生成自动修复建议
    if field_missing:
        from datetime import date
        defaults = {
            "活跃 Change": "无",
            "当前阶段": "无",
            "当前任务": "无",
            "中断任务": "无",
            "Pipeline 待续": "无",
            "并行 Change": "无",
            "更新时间": date.today().isoformat(),
        }
        fix_fields = {}
        for f in field_missing:
            if f in defaults:
                fix_fields[f] = defaults[f]
        fixes.append({
            "action": "补充缺失字段",
            "fields": fix_fields,
        })

    passed = len(missing) == 0
    return {
        "passed": passed,
        "missing": missing,
        "warnings": warnings,
        "info": info,
        "fields": fields,
        "fixes": fixes,
    }


def main():
    parser = argparse.ArgumentParser(description="STATE.md 完整性校验器")
    parser.add_argument("--state-file", required=True, help="STATE.md 文件路径")
    parser.add_argument("--specs-dir", help=".specs/ 目录路径（可选，用于验证目录存在性）")
    args = parser.parse_args()

    result = validate(args.state_file, args.specs_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
