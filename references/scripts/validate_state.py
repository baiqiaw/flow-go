#!/usr/bin/env python3
"""STATE.md 完整性校验器 — 自动化校验，减少模型判断负担

用法：
  # 校验项目级 STATE.md + 所有活跃 change 的 per-change STATE
  python3 validate_state.py --state-file <path> --specs-dir <path>

  # 仅校验指定 change 的 per-change STATE
  python3 validate_state.py --state-file <path> --specs-dir <path> --change-id <id>

结构：
  - 项目级 STATE.md：Pipeline 待续 + 更新时间（活跃 change 通过 git worktree list 发现）
  - .specs/<id>/STATE.md（change 级详情）：当前阶段 + 当前任务 + 中断任务 + 阶段进度 + 更新时间

校验规则来自 meta-artifacts.md「完整性校验」清单。
输出 JSON 格式的校验结果，供 flow-go 第一步读取。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime

# === 项目级 STATE.md 必填字段 ===
PROJECT_REQUIRED_FIELDS = [
    "Pipeline 待续",
    "更新时间",
]

# === per-change STATE.md 必填字段 ===
CHANGE_REQUIRED_FIELDS = [
    "当前阶段",
    "路径模式",
    "当前任务",
    "中断任务",
    "阶段进度",
    "更新时间",
]

VALID_STAGES = [
    "0-需求", "1-设计", "2-任务", "3-开发",
    "4-测试", "5-审查", "6-部署", "7-验收",
]

VALID_PATH_MODES = ["完整", "增量", "最短"]

def parse_state(state_path):
    """解析 STATE.md 为字段字典（兼容列表格式和表格格式）"""
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
                # 匹配列表值（旧格式）
                if current_key and line.startswith("- "):
                    val = line[2:].strip()
                    if current_key not in fields:
                        fields[current_key] = val
                    else:
                        # 多值字段用逗号拼接
                        fields[current_key] += "," + val
                    continue
                # 匹配表格行（新格式：| change-id | 阶段 | 最后更新 |）
                if current_key and line.startswith("|") and re.match(r"^\|[\s\-:|]+\|$", line.strip()):
                    # 跳过分隔行（|---|---|）
                    continue
                if current_key and line.startswith("|"):
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    if current_key not in fields:
                        fields[current_key] = [cells]
                    else:
                        fields[current_key].append(cells)
                    continue
                # 匹配纯文本值（per-change STATE.md 格式：## 标题后跟纯文本）
                if current_key and line.strip() and not line.startswith("#"):
                    val = line.strip()
                    if current_key not in fields:
                        fields[current_key] = val
                    else:
                        fields[current_key] += "," + val
    except (OSError, UnicodeDecodeError) as e:
        return None, [f"无法读取文件：{e}"]
    return fields, []


def discover_active_changes(project_dir):
    """通过 git worktree list 发现活跃 change。

    Returns:
        tuple: (changes: list[dict], warnings: list[str])
            changes: 每个 dict 含 'change_id' 和 'worktree_path'
            warnings: 异常时的警告信息
    """
    import subprocess
    try:
        result = subprocess.run(
            ['git', 'worktree', 'list', '--porcelain'],
            capture_output=True, text=True, cwd=project_dir
        )
        if result.returncode != 0:
            return [], [f"git worktree list 执行失败：{result.stderr.strip()}"]
        changes = []
        current_path = None
        for line in result.stdout.strip().split('\n'):
            if line.startswith('worktree '):
                current_path = line[len('worktree '):]
            elif line.startswith('branch ') and 'refs/heads/change/' in line:
                change_id = line.split('/')[-1]
                if current_path:
                    changes.append({'change_id': change_id, 'worktree_path': current_path})
        return changes, []
    except FileNotFoundError:
        return [], ["git 命令不可用，跳过 worktree 发现"]
    except OSError as e:
        return [], [f"worktree 发现异常：{e}"]


def validate_change_state(change_state_path, change_id):
    """校验 per-change STATE.md (.specs/<id>/STATE.md) 的完整性

    参数：
        change_state_path: .specs/<id>/STATE.md 的路径
        change_id: change-id 标识符（用于错误消息）
    返回：校验结果字典
    """
    errors = []
    warnings = []
    info = []

    if not os.path.isfile(change_state_path):
        return {"passed": False, "errors": [f"change '{change_id}' 的 STATE.md 不存在：{change_state_path}"], "warnings": [], "fields": {}, "fixes": []}

    with open(change_state_path, encoding="utf-8") as f:
        content = f.read()
    if not content.strip():
        return {"passed": False, "errors": [f"change '{change_id}' 的 STATE.md 为空"], "warnings": [], "fields": {}, "fixes": []}

    fields, parse_errors = parse_state(change_state_path)
    if parse_errors:
        return {"passed": False, "errors": parse_errors, "warnings": [], "fields": {}, "fixes": []}

    # 校验 per-change 必填字段
    missing = [f for f in CHANGE_REQUIRED_FIELDS if f not in fields]
    if missing:
        errors.append(f"change '{change_id}' 缺少必填字段：{', '.join(missing)}")

    # 校验当前阶段合法
    stage = fields.get("当前阶段", "")
    if isinstance(stage, str) and stage and stage != "无" and stage not in VALID_STAGES:
        errors.append(f"change '{change_id}' 当前阶段 '{stage}' 不在合法值中：{VALID_STAGES}")

    # 校验路径模式合法
    path_mode = fields.get("路径模式", "")
    if isinstance(path_mode, str) and path_mode and path_mode not in VALID_PATH_MODES:
        errors.append(f"change '{change_id}' 路径模式 '{path_mode}' 不在合法值中：{VALID_PATH_MODES}")

    # 校验中断任务和当前任务不重复
    cur_task = fields.get("当前任务", "")
    int_task = fields.get("中断任务", "")
    cur_str = cur_task if isinstance(cur_task, str) else str(cur_task)
    int_str = int_task if isinstance(int_task, str) else str(int_task)
    if cur_str and int_str and cur_str != "无" and int_str != "无" and cur_str == int_str:
        errors.append(f"change '{change_id}' 当前任务和中断任务相同：{cur_str}")

    # 校验更新时间格式
    update_time = fields.get("更新时间", "")
    if isinstance(update_time, str) and update_time and update_time != "无":
        try:
            datetime.strptime(update_time, "%Y-%m-%d")
        except ValueError:
            errors.append(f"change '{change_id}' 更新时间格式不正确：'{update_time}'，应为 YYYY-MM-DD")

    fixes = []
    if missing:
        from datetime import date
        defaults = {
            "当前阶段": "无",
            "路径模式": "完整",
            "当前任务": "无",
            "中断任务": "无",
            "阶段进度": "无",
            "更新时间": date.today().isoformat(),
        }
        fix_fields = {f: defaults[f] for f in missing if f in defaults}
        fixes.append({"action": f"补充 change '{change_id}' 缺失字段", "fields": fix_fields})

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "fields": fields,
        "fixes": fixes,
    }


def validate(state_path, specs_dir=None, change_id=None):
    """执行完整性校验，返回结果字典

    校验逻辑：
    1. 校验项目级 STATE.md 基本字段（Pipeline 待续 + 更新时间）
    2. 通过 git worktree list 发现活跃 change
    3. 校验每个活跃 change 的 per-change STATE.md
    4. change_id 参数可限定仅校验指定 change
    """
    errors = []
    warnings = []
    info = []

    # === 项目级 STATE.md 基本校验 ===
    if not os.path.isfile(state_path):
        return {"passed": False, "errors": ["STATE.md 文件不存在"], "warnings": [], "fields": {}, "fixes": [],
                "change_results": {}}

    with open(state_path, encoding="utf-8") as f:
        content = f.read()
    if not content.strip():
        return {"passed": False, "errors": ["STATE.md 文件为空"], "warnings": [], "fields": {}, "fixes": [],
                "change_results": {}}

    # 校验首行包含 STATE
    first_line = content.split("\n")[0]
    if "STATE" not in first_line:
        errors.append(f"首行不包含 'STATE'：{first_line}")

    # 解析字段
    fields, parse_errors = parse_state(state_path)
    if parse_errors:
        return {"passed": False, "errors": parse_errors, "warnings": [], "fields": {}, "fixes": [],
                "change_results": {}}

    fixes = []

    # === 项目级字段校验 ===
    missing = [f for f in PROJECT_REQUIRED_FIELDS if f not in fields]
    if missing:
        errors.append(f"缺少必填字段：{', '.join(missing)}")

    # Pipeline 待续验证（宽松）
    pipeline = fields.get("Pipeline 待续", "")
    if isinstance(pipeline, str) and pipeline and pipeline != "无":
        warnings.append(f"Pipeline 待续非空：{pipeline}，请确认对应 change-id 存在")

    # 更新时间格式
    update_time = fields.get("更新时间", "")
    if isinstance(update_time, str) and update_time and update_time != "无":
        try:
            datetime.strptime(update_time, "%Y-%m-%d")
        except ValueError:
            errors.append(f"更新时间格式不正确：'{update_time}'，应为 YYYY-MM-DD")

    # 生成修复建议
    if missing:
        from datetime import date
        defaults = {
            "Pipeline 待续": "无",
            "更新时间": date.today().isoformat(),
        }
        fix_fields = {f: defaults[f] for f in missing if f in defaults}
        fixes.append({"action": "补充缺失字段", "fields": fix_fields})

    # === 通过 git worktree list 发现活跃 change ===
    project_dir = os.path.dirname(state_path)
    active_changes, wt_warnings = discover_active_changes(project_dir)
    warnings.extend(wt_warnings)

    # change_id 限定：仅校验指定 change
    if change_id:
        matched = [c for c in active_changes if c['change_id'] == change_id]
        if not matched:
            errors.append(f"指定校验的 change-id '{change_id}' 不在活跃 worktree 列表中")
            # 仍然尝试校验该目录
            active_changes = [{'change_id': change_id, 'worktree_path': None}]
        else:
            active_changes = matched

    # === per-change STATE.md 校验 ===
    change_results = {}
    for change_info in active_changes:
        cid = change_info['change_id']
        # 路径遍历防护
        if ".." in cid or "/" in cid or "\\" in cid:
            errors.append(f"change-id '{cid}' 包含非法路径字符")
            continue
        if not specs_dir:
            continue
        change_dir = os.path.join(specs_dir, cid)
        if not os.path.isdir(change_dir):
            errors.append(f"活跃 Change '{cid}' 对应的 .specs/{cid}/ 目录不存在")
            continue
        # 校验 per-change STATE.md
        change_state_path = os.path.join(change_dir, "STATE.md")
        cresult = validate_change_state(change_state_path, cid)
        change_results[cid] = cresult
        if not cresult["passed"]:
            errors.extend(cresult["errors"])
        warnings.extend(cresult["warnings"])
        fixes.extend(cresult["fixes"])

    passed = len(missing) == 0 and len(errors) == 0
    return {
        "passed": passed,
        "missing": missing,
        "warnings": warnings,
        "info": info,
        "fields": fields,
        "fixes": fixes,
        "change_results": change_results,
    }


def main():
    parser = argparse.ArgumentParser(description="STATE.md 完整性校验器（两层结构）")
    parser.add_argument("--state-file", required=True, help="项目级 STATE.md 文件路径")
    parser.add_argument("--specs-dir", help=".specs/ 目录路径（用于校验 per-change STATE 和目录存在性）")
    parser.add_argument("--change-id", help="仅校验指定 change 的 per-change STATE（可选，不传时校验全部活跃 change）")
    args = parser.parse_args()

    result = validate(args.state_file, args.specs_dir, args.change_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
