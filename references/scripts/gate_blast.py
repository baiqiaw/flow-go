#!/usr/bin/env python3
"""Blast radius 检查 — 统计 git diff 改动文件数

从 gate_check.py 提取的 check_blast_radius()。
"""
import os
import subprocess


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
