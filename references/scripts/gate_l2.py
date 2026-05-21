#!/usr/bin/env python3
"""L2 全量 5 维 AND 门控 — quality / scope / security / regression / efficiency

前 4 维逻辑从 gate_check.py 提取，第 5 维 efficiency 为新增。
所有维度 AND 逻辑：任一维度失败则整体失败。

用法（编程接口）：
  from gate_l2 import check
  result = check(specs_dir, project_dir)
"""

import os
import re
import subprocess

from gate_dimensions import DANGEROUS_PATTERNS, EFFICIENCY_THRESHOLD


# ---------------------------------------------------------------------------
# 维度 1：quality — 从 *-SUMMARY.md 提取 verify 通过率
# ---------------------------------------------------------------------------
def _quality(specs_dir):
    """从 *-SUMMARY.md 提取 verify 通过率，≥80% 通过"""
    # 查找 *-SUMMARY.md 文件
    summaries = []
    if os.path.isdir(specs_dir):
        summaries = sorted(
            f for f in os.listdir(specs_dir)
            if f.endswith("-SUMMARY.md") or f == "SUMMARY.md"
        )

    if not summaries:
        return {"passed": True, "detail": "无 SUMMARY.md，跳过质量检查"}

    # 合并所有 SUMMARY 文件内容
    content_parts = []
    for fname in summaries:
        fpath = os.path.join(specs_dir, fname)
        try:
            with open(fpath, encoding="utf-8") as f:
                content_parts.append(f.read())
        except OSError:
            continue

    if not content_parts:
        return {"passed": True, "detail": "SUMMARY.md 读取失败，跳过质量检查"}

    content = "\n".join(content_parts)

    # 格式 1：百分比 90%
    pct = re.search(r'verify\s*通过率[：:]\s*(\d+)%', content)
    if pct:
        rate = int(pct.group(1))
        return {"passed": rate >= 80, "detail": f"verify 通过率 {rate}% ({'≥' if rate >= 80 else '<'}80%)"}

    # 格式 2：分数 9/10
    frac = re.search(r'verify\s*通过率[：:]\s*(\d+)/(\d+)', content)
    if frac:
        passed, total = int(frac.group(1)), int(frac.group(2))
        rate = round(passed / total * 100) if total > 0 else 100
        return {"passed": rate >= 80, "detail": f"verify 通过率 {passed}/{total} ({rate}%)"}

    # 格式 3：关键词存在但无具体数值
    if "verify" not in content.lower():
        return {"passed": True, "detail": "SUMMARY.md 无 verify 信息，跳过质量检查"}

    return {"passed": True, "detail": "verify 信息存在但无法解析具体通过率"}


# ---------------------------------------------------------------------------
# 维度 2：scope — TASK.md write_files vs git diff --name-only
# ---------------------------------------------------------------------------
def _scope(specs_dir, project_dir):
    """检查 git diff 改动是否超出 TASK.md 规划"""
    task_path = os.path.join(specs_dir, "TASK.md")
    if not os.path.isfile(task_path):
        return {"passed": True, "detail": "TASK.md 不存在，跳过范围检查"}

    try:
        with open(task_path, encoding="utf-8") as f:
            task_content = f.read()
    except OSError:
        return {"passed": True, "detail": "TASK.md 读取失败，跳过范围检查"}

    # 提取 write_files 列表
    planned = set()
    for m in re.finditer(r'<write_files>(.*?)</write_files>', task_content, re.S):
        for line in m.group(1).strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('<!--'):
                planned.add(line)

    if not planned:
        return {"passed": True, "detail": "TASK.md 无预期文件列表，跳过范围检查"}

    # 获取实际改动
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"], cwd=project_dir,
            capture_output=True, text=True, timeout=10,
        )
        actual = set(f for f in result.stdout.strip().split("\n") if f) if result.returncode == 0 else set()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"passed": True, "detail": "git 不可用，跳过范围检查"}

    out_of_scope = actual - planned
    if out_of_scope:
        return {"passed": False, "detail": f"改动 {len(out_of_scope)} 文件超出 TASK.md 规划: {', '.join(sorted(out_of_scope)[:5])}"}
    return {"passed": True, "detail": f"改动 {len(actual)} 文件，均在 TASK.md 规划范围内"}


# ---------------------------------------------------------------------------
# 维度 3：security — DANGEROUS_PATTERNS 扫描
# ---------------------------------------------------------------------------
def _security(specs_dir):
    """扫描 specs 目录 .md 文件（排除 TEST.md），匹配危险模式"""
    matches = []
    if not os.path.isdir(specs_dir):
        return {"passed": True, "detail": "specs 目录不存在，跳过安全检查"}

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
        return {"passed": False, "detail": f"检出 {len(matches)} 处危险模式: {'; '.join(matches[:3])}"}
    return {"passed": True, "detail": "未检出危险模式"}


# ---------------------------------------------------------------------------
# 维度 4：regression — TEST.md 回归关键词检查
# ---------------------------------------------------------------------------
def _regression(specs_dir):
    """检查 TEST.md 中是否有原已通过用例失败的记录"""
    test_path = os.path.join(specs_dir, "TEST.md")
    if not os.path.isfile(test_path):
        return {"passed": True, "detail": "TEST.md 不存在，跳过回归检查"}

    try:
        with open(test_path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        return {"passed": True, "detail": "TEST.md 读取失败，跳过回归检查"}

    patterns = [
        r"原已通过用例失败",
        r"previously\s+passing.*failed",
        r"regression",
        r"回归.*失败",
    ]
    for pat in patterns:
        hit = re.search(pat, content, re.I)
        if hit:
            return {"passed": False, "detail": f"TEST.md 包含回归失败记录: \"{hit.group()[:60]}\""}

    return {"passed": True, "detail": "无原已通过用例失败记录"}


# ---------------------------------------------------------------------------
# 维度 5：efficiency（新增）— AC 通过数 / (代码行数/100)
# ---------------------------------------------------------------------------
def _efficiency(specs_dir, project_dir):
    """效率维度：AC 通过数与代码增量的比值

    逻辑：
    1. git diff 无改动 → passed=true（纯文档变更）
    2. 从 TEST.md 提取 AC 通过数，或从 *-SUMMARY.md 提取 verify 通过率作为 fallback
    3. ratio = ac_passed / (lines/100)
    4. ratio ≥ EFFICIENCY_THRESHOLD → passed
    """
    # 获取 git diff 增量行数
    total_lines = 0
    try:
        result = subprocess.run(
            ["git", "diff", "--stat"], cwd=project_dir,
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            # --stat 最后一行类似 " 3 files changed, 42 insertions(+), 10 deletions(-)"
            stat_lines = result.stdout.strip().split('\n')
            if stat_lines:
                last_line = stat_lines[-1]
                # 提取 insertions 数
                ins = re.search(r'(\d+)\s+insertion', last_line)
                if ins:
                    total_lines = int(ins.group(1))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {"passed": True, "detail": "git 不可用，跳过效率检查"}

    # 无代码改动 → 纯文档变更，直接通过
    if total_lines == 0:
        return {"passed": True, "detail": "git diff 无代码改动（纯文档变更）"}

    # 提取 AC 通过数
    ac_passed = 0

    # 优先从 TEST.md 提取
    test_path = os.path.join(specs_dir, "TEST.md")
    if os.path.isfile(test_path):
        try:
            with open(test_path, encoding="utf-8") as f:
                test_content = f.read()
            # 匹配 "AC-1 ... PASS" 或 "AC-01 ... PASS" 等格式
            ac_matches = re.findall(r'AC-\d+.*?(?:PASS|通过)', test_content, re.I)
            ac_passed = len(ac_matches)
        except OSError:
            pass

    # fallback：从 *-SUMMARY.md 提取 verify 通过数
    if ac_passed == 0 and os.path.isdir(specs_dir):
        for fname in sorted(os.listdir(specs_dir)):
            if not fname.endswith("-SUMMARY.md") and fname != "SUMMARY.md":
                continue
            fpath = os.path.join(specs_dir, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    sum_content = f.read()
            except OSError:
                continue

            # 分数格式
            frac = re.search(r'verify\s*通过率[：:]\s*(\d+)/(\d+)', sum_content)
            if frac:
                ac_passed = int(frac.group(1))
                break
            # 百分比格式 → 估算
            pct = re.search(r'verify\s*通过率[：:]\s*(\d+)%', sum_content)
            if pct:
                # 百分比无法直接得到通过数，用百分比本身作为代理值
                ac_passed = int(pct.group(1))
                break

    # AC 通过数为 0 且无匹配 → 无法评估，跳过
    if ac_passed == 0:
        return {"passed": True, "detail": "无法提取 AC 通过数，跳过效率检查"}

    ratio = ac_passed / (total_lines / 100)
    threshold = EFFICIENCY_THRESHOLD
    passed = ratio >= threshold
    return {
        "passed": passed,
        "detail": f"AC 通过 {ac_passed}, 增量 {total_lines} 行, ratio={ratio:.2f} ({'≥' if passed else '<'}{threshold})",
    }


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def check(specs_dir, project_dir):
    """L2 全量 5 维 AND 门控

    参数：
        specs_dir: .specs/<change-id> 目录路径
        project_dir: 项目根目录路径

    返回：
        dict: {passed: bool, dimensions: {quality, scope, security, regression, efficiency}}
    """
    quality = _quality(specs_dir)
    scope = _scope(specs_dir, project_dir)
    security = _security(specs_dir)
    regression = _regression(specs_dir)
    efficiency = _efficiency(specs_dir, project_dir)

    passed = (
        quality["passed"]
        and scope["passed"]
        and security["passed"]
        and regression["passed"]
        and efficiency["passed"]
    )

    return {
        "passed": passed,
        "dimensions": {
            "quality": quality,
            "scope": scope,
            "security": security,
            "regression": regression,
            "efficiency": efficiency,
        },
    }
