"""flow-go 测试共享 fixture"""
import os
import sys
from pathlib import Path

import pytest

# 将脚本目录加入 sys.path，支持 import 脚本模块
SCRIPTS_DIR = str(Path(__file__).parent.parent / "references" / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

SKILL_ROOT = str(Path(__file__).parent.parent)


@pytest.fixture
def skill_root():
    """flow-go skill 根目录"""
    return SKILL_ROOT


@pytest.fixture
def tmp_project(tmp_path):
    """模拟项目目录结构：含 .specs/<id>/ 和 STATE.md"""
    specs_dir = tmp_path / ".specs" / "TEST-001"
    specs_dir.mkdir(parents=True)
    (specs_dir / "STATE.md").write_text(
        "# STATE — TEST-001\n\n## 当前阶段\n3-开发\n\n## 路径模式\n完整\n\n"
        "## 当前任务\nT01\n\n## 中断任务\n无\n\n## 阶段进度\n无\n\n## 更新时间\n2026-05-23\n",
        encoding="utf-8",
    )
    (tmp_path / "STATE.md").write_text(
        "# STATE\n\n## 活跃 Change\n| change-id | 阶段 | 最后更新 |\n"
        "|-----------|------|---------|\n| TEST-001 | 3-开发 | 2026-05-23 |\n\n"
        "## Pipeline 待续\n- 无\n\n## 更新时间\n- 2026-05-23\n",
        encoding="utf-8",
    )
    return tmp_path
