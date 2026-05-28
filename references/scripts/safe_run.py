#!/usr/bin/env python3
"""flow-go 脚本安全运行包装器

统一入口：捕获子脚本异常、超时保护、友好错误提示、错误遥测日志。

用法：
  python3 safe_run.py --script gate_check.py --timeout 30 -- --stage 3 --change-id X ...
  python3 safe_run.py --script validate_state.py --critical -- --state-file STATE.md ...

输出（stdout）：结构化 JSON
  {status: "ok"|"error"|"timeout", exit_code: N, stdout: "...", stderr: "...",
   hint: "...", recovery: "retry"|"skip"|"degrade"|"manual"}

自身永不崩溃，始终输出有效 JSON。
"""
import argparse
import json
import os
import re
import signal
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path


SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

ERROR_PATTERNS = [
    (r"FileNotFoundError.*: '[^']*'", "缺少文件", "worktree 未正确创建或文件路径无效"),
    (r"json\.decoder\.JSONDecodeError", "JSON 格式异常", "运行 validate_state.py 检查对应文件格式"),
    (r"ModuleNotFoundError.*No module named '([^']+)'", "缺少 Python 依赖 {module}", "pip install {module}"),
    (r"PermissionError.*: '[^']*'", "权限不足", "检查文件权限或是否被其他进程占用"),
    (r"KeyError.*: '([^']+)'", "脚本内部异常 (KeyError: {key})", "STATE.md 格式可能已变更，运行 validate_state.py 检查"),
    (r"AttributeError.*: '([^']+)'", "脚本内部异常 (AttributeError: {attr})", "可能是数据结构变更导致，检查对应工件格式"),
    (r"IsADirectoryError", "路径是目录而非文件", "检查路径参数是否正确"),
    (r"NotADirectoryError", "路径不是目录", "检查目录参数是否正确"),
    (r"ConnectionRefusedError|ConnectionError", "网络连接失败", "检查网络和服务状态"),
]


def _has_traceback(stderr_text):
    """检查 stderr 是否包含 Python traceback（真正的崩溃），还是只是业务错误输出"""
    if not stderr_text.strip():
        return False
    return "Traceback (most recent call last)" in stderr_text


def _match_error(stderr_text):
    """匹配 stderr 文本，返回 (hint, recovery)"""
    stderr_lower = stderr_text.lower()
    for pattern, hint_tmpl, recovery_tmpl in ERROR_PATTERNS:
        m = re.search(pattern, stderr_text, re.IGNORECASE)
        if m:
            groups = m.groups()
            hint = hint_tmpl
            recovery = "manual"
            if "{module}" in hint:
                hint = hint.replace("{module}", groups[0] if groups else "?")
            if "{key}" in hint:
                hint = hint.replace("{key}", groups[0] if groups else "?")
            if "{attr}" in hint:
                hint = hint.replace("{attr}", groups[0] if groups else "?")

            if "pip install" in recovery_tmpl:
                recovery_tmpl = recovery_tmpl.replace("{module}", groups[0] if groups else "?")

            # recovery 判定
            if "缺少文件" in hint or "权限不足" in hint or "路径" in hint:
                recovery = "degrade"
            elif "JSON 格式" in hint or "KeyError" in hint or "AttributeError" in hint:
                recovery = "degrade"
            elif "依赖" in hint:
                recovery = "manual"
            elif "网络" in hint:
                recovery = "retry"

            return hint, recovery

    # 通用匹配
    if "traceback" in stderr_lower or "error" in stderr_lower:
        last_line = [l for l in stderr_text.strip().split("\n") if l.strip()][-1] if stderr_text.strip() else ""
        return f"脚本异常退出: {last_line[:120]}", "degrade"

    return None, "degrade"


def _log_error(script_name, error_type, stderr_preview, recovery, change_id="", stage=""):
    """追加错误记录到 skill-errors.jsonl

    环境变量 FLOWGO_ERROR_LOG 可重定向日志路径（测试隔离用），
    设为空字符串时禁用写入。
    """
    env_log = os.environ.get("FLOWGO_ERROR_LOG")
    if env_log == "":
        return

    if env_log:
        log_path = env_log
    else:
        specs_dir = None
        cwd = os.getcwd()

        for candidate in [cwd, os.path.dirname(cwd)]:
            sp = os.path.join(candidate, ".specs")
            if os.path.isdir(sp):
                specs_dir = sp
                break

        if specs_dir:
            log_path = os.path.join(specs_dir, "skill-errors.jsonl")
        else:
            log_path = os.path.join(cwd, "skill-errors.jsonl")

    record = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "change_id": change_id,
        "stage": stage,
        "script": script_name,
        "error_type": error_type,
        "stderr_preview": stderr_preview[:200],
        "recovery": recovery,
    }
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass


def run_script(script_name, args, timeout=30):
    """执行子脚本，返回 (exit_code, stdout, stderr, timed_out)"""
    script_path = os.path.join(SCRIPTS_DIR, script_name)
    cmd = [sys.executable, script_path] + args

    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
            cwd=os.getcwd(), env=os.environ.copy(),
        )
        return proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired:
        return -1, "", f"脚本执行超时（{timeout}s）", True
    except FileNotFoundError:
        return -2, "", f"脚本文件不存在: {script_path}", False
    except OSError as e:
        return -3, "", f"系统错误: {e}", False


def main():
    parser = argparse.ArgumentParser(
        description="flow-go 脚本安全运行包装器",
        usage="python3 safe_run.py --script <name> [--timeout N] [--critical] -- <子脚本参数>",
    )
    parser.add_argument("--script", required=True, help="子脚本文件名（如 gate_check.py）")
    parser.add_argument("--timeout", type=int, default=30, help="超时秒数（默认 30）")
    parser.add_argument("--critical", action="store_true", help="标记为关键脚本，失败时 recovery=manual")
    parser.add_argument("--change-id", default="", help="当前 change-id（用于错误日志）")
    parser.add_argument("--stage", default="", help="当前阶段（用于错误日志）")
    parser.add_argument("child_args", nargs=argparse.REMAINDER, help="子脚本参数（-- 之后）")

    args = parser.parse_args()

    # 去掉前导的 "--"（argparse REMAINDER 会保留）
    if args.child_args and args.child_args[0] == "--":
        child_args = args.child_args[1:]
    else:
        child_args = args.child_args

    script_name = args.script
    timeout = args.timeout

    try:
        exit_code, stdout, stderr, timed_out = run_script(script_name, child_args, timeout)

        if timed_out:
            hint = f"脚本 {script_name} 执行超时（{timeout}s）"
            recovery = "retry"
            error_type = "Timeout"
            result = {
                "status": "timeout",
                "exit_code": -1,
                "stdout": stdout,
                "stderr": stderr,
                "hint": hint,
                "recovery": recovery,
            }
            _log_error(script_name, error_type, stderr[:200], recovery, args.change_id, args.stage)

        elif exit_code == 2 and "can't open file" in stderr.lower():
            # Python 解释器找到了但脚本文件不存在（subprocess 返回 exit 2）
            hint = f"脚本文件不存在: references/scripts/{script_name}"
            recovery = "degrade"
            error_type = "MissingFile"
            result = {
                "status": "error",
                "exit_code": 2,
                "stdout": "",
                "stderr": stderr,
                "hint": hint,
                "recovery": recovery,
            }
            _log_error(script_name, error_type, stderr[:200], recovery, args.change_id, args.stage)

        elif exit_code == -2:
            # Python 解释器不存在（subprocess.run 抛出 FileNotFoundError）
            hint = f"Python 解释器不可用，无法执行 {script_name}"
            recovery = "manual"
            error_type = "PythonMissing"
            result = {
                "status": "error",
                "exit_code": -2,
                "stdout": "",
                "stderr": stderr,
                "hint": hint,
                "recovery": recovery,
            }
            _log_error(script_name, error_type, stderr[:200], recovery, args.change_id, args.stage)

        elif exit_code == -3:
            # 系统级错误（OSError）
            hint = f"系统错误，无法执行 {script_name}: {stderr}"
            recovery = "manual"
            error_type = "SystemError"
            result = {
                "status": "error",
                "exit_code": -3,
                "stdout": "",
                "stderr": stderr,
                "hint": hint,
                "recovery": recovery,
            }
            _log_error(script_name, error_type, stderr[:200], recovery, args.change_id, args.stage)

        elif exit_code == 0 or (exit_code != 0 and not _has_traceback(stderr)):
            # exit_code=0 或 exit_code≠0 但 stderr 无 traceback → 脚本正常执行
            result = {
                "status": "ok",
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "hint": "",
                "recovery": "",
            }

        else:
            hint, recovery = _match_error(stderr)
            if hint is None:
                hint = f"脚本 {script_name} 异常退出 (exit={exit_code})"
            if args.critical:
                recovery = "manual"

            error_type = "ScriptError"
            result = {
                "status": "error",
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "hint": hint,
                "recovery": recovery,
            }
            _log_error(script_name, error_type, stderr[:200], recovery, args.change_id, args.stage)

        # 输出结构化 JSON
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        # safe_run.py 自身的最后防线
        fallback = {
            "status": "error",
            "exit_code": -99,
            "stdout": "",
            "stderr": f"safe_run.py 自身异常: {e}",
            "hint": f"脚本包装器内部错误: {e}",
            "recovery": "manual",
        }
        print(json.dumps(fallback, ensure_ascii=False, indent=2))
        try:
            _log_error("safe_run.py", "WrapperError", str(e)[:200], "manual", args.change_id, args.stage)
        except Exception:
            pass


if __name__ == "__main__":
    main()
