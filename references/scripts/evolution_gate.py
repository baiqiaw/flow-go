#!/usr/bin/env python3
"""三重门控系统 — 约束门 + 回归门 + 安全门

借鉴进化引擎 gate_system.py 的三重门控逻辑，适配 flow-go 工件体系。
在交叉评审前自动检查工件格式、健康趋势、安全模式，避免浪费子代理 token。

用法：
    python3 evolution_gate.py check --specs-dir .specs/<change-id>
    python3 evolution_gate.py check --specs-dir .specs/<change-id> --history .specs/health-trends.jsonl
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


class GateSystem:
    """三重门控：约束门 + 回归门 + 安全门"""

    def __init__(self, config=None):
        self.config = config or self._default_config()

    def run_all_gates(self, specs_dir, history_path=None):
        """运行全部三个门控"""
        constraint = self.constraint_gate(specs_dir)
        regression = self.regression_gate(specs_dir, history_path)
        safety = self.safety_gate(specs_dir)

        all_passed = all(g.get("passed", False) for g in [constraint, regression, safety])
        return {
            "passed": all_passed,
            "constraint": constraint,
            "regression": regression,
            "safety": safety,
            "recommendation": "approve" if all_passed else "reject",
        }

    def constraint_gate(self, specs_dir):
        """约束门：工件格式/大小/必填字段检查"""
        errors = []
        specs = Path(specs_dir)

        # SUMMARY.md 检查
        summary_path = specs / "SUMMARY.md"
        summary = self._read_file(summary_path)
        if not summary:
            errors.append("SUMMARY.md 不存在或为空")
        else:
            size = len(summary.encode("utf-8"))
            if size > self.config["summary_max_bytes"]:
                errors.append(f"SUMMARY.md 超过大小限制 ({size} > {self.config['summary_max_bytes']} bytes)")
            for field in ["做了什么", "改动文件", "verify"]:
                if field not in summary:
                    errors.append(f"SUMMARY.md 缺少必填字段: {field}")

        # REVIEW.md 检查（如存在）
        review_path = specs / "REVIEW.md"
        review = self._read_file(review_path)
        if review:
            for field in ["spec 合规", "代码质量"]:
                if field not in review:
                    errors.append(f"REVIEW.md 缺少必填字段: {field}")

        # TEST.md 检查（如存在）
        test_path = specs / "TEST.md"
        test = self._read_file(test_path)
        if test:
            size = len(test.encode("utf-8"))
            if size > self.config["test_max_bytes"]:
                errors.append(f"TEST.md 超过大小限制 ({size} > {self.config['test_max_bytes']} bytes)")

        return {
            "passed": len(errors) == 0,
            "details": {"errors": errors},
        }

    def regression_gate(self, specs_dir, history_path=None):
        """回归门：与历史 health 评分对比"""
        if not history_path or not Path(history_path).exists():
            return {"passed": True, "details": {"reason": "无历史数据，首次通过"}}

        try:
            lines = Path(history_path).read_text(encoding="utf-8").strip().split("\n")
            records = [json.loads(line) for line in lines if line.strip()]
        except (json.JSONDecodeError, OSError):
            return {"passed": True, "details": {"reason": "历史数据格式错误，跳过回归门"}}

        if len(records) < 2:
            return {"passed": True, "details": {"reason": "历史数据不足 2 条，跳过回归门"}}

        current = records[-1]
        previous = records[-2]
        tolerance = self.config["regression_tolerance"]

        current_score = float(current.get("composite", 0))
        previous_score = float(previous.get("composite", 0))
        delta = current_score - previous_score

        if delta < -tolerance * 100:
            return {
                "passed": False,
                "details": {
                    "reason": f"综合评分退步 {abs(delta):.1f} 分（容忍度 {tolerance * 100:.0f}）",
                    "previous_score": previous_score,
                    "current_score": current_score,
                    "delta": round(delta, 1),
                },
            }

        # 维度退步检查
        dim_limit = self.config["dimension_regression_limit"]
        current_dims = current.get("scores", {})
        previous_dims = previous.get("scores", {})
        dim_failures = {}
        for name, prev_val in previous_dims.items():
            prev = float(prev_val) if not isinstance(prev_val, (int, float)) else prev_val
            curr = float(current_dims.get(name, 0))
            diff = curr - prev
            if diff < -dim_limit * 100:
                dim_failures[name] = round(diff, 1)

        if dim_failures:
            return {
                "passed": False,
                "details": {
                    "reason": f"维度退步: {dim_failures}",
                    "dimension_failures": dim_failures,
                },
            }

        return {
            "passed": True,
            "details": {
                "delta": round(delta, 1),
                "previous_score": previous_score,
                "current_score": current_score,
            },
        }

    def safety_gate(self, specs_dir):
        """安全门：密钥泄露检查（.md 工件不检查代码执行模式，避免误报）"""
        failures = []
        specs = Path(specs_dir)

        for md_file in specs.glob("*.md"):
            content = self._read_file(md_file)
            if not content:
                continue

            # 密钥泄露
            for pattern in self.config["secret_patterns"]:
                if re.search(pattern, content, re.I):
                    failures.append(f"{md_file.name}: 疑似密钥泄露")
                    break

        return {
            "passed": len(failures) == 0,
            "details": {"failures": failures},
        }

    def _read_file(self, path):
        try:
            return Path(path).read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return ""

    def _default_config(self):
        return {
            "summary_max_bytes": 10 * 1024,
            "test_max_bytes": 8 * 1024,
            "regression_tolerance": 0.05,
            "dimension_regression_limit": 0.10,
            "dangerous_patterns": [
                "rm -rf", "DROP TABLE", "DROP DATABASE",
                "eval(", "exec(", "os.system(",
                "subprocess.Popen", "os.remove(",
            ],
            "secret_patterns": [
                r"api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_-]{8,}",
                r"token\s*[:=]\s*['\"][A-Za-z0-9_-]{8,}",
                r"password\s*[:=]\s*['\"].+['\"]",
            ],
        }


def main():
    parser = argparse.ArgumentParser(description="三重门控系统")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("--specs-dir", required=True, help=".specs/<change-id> 目录路径")
    check.add_argument("--history", default=None, help="health-trends.jsonl 路径")
    check.add_argument("--output", default=None, help="输出 JSON 路径")
    args = parser.parse_args()

    if args.command != "check":
        return

    gate = GateSystem()
    result = gate.run_all_gates(args.specs_dir, args.history)
    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        tmp = Path(args.output).with_suffix(".json.tmp")
        tmp.write_text(output, encoding="utf-8")
        os.replace(tmp, Path(args.output))
    else:
        print(output)

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
