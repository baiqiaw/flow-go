"""flow-go 脚本共享路径工具

统一路径推导逻辑，消除各脚本中重复且不一致的 __file__ / CWD 推导。
"""
import os
import sys
from pathlib import Path


def resolve_project_root(specs_dir: str) -> str:
    """从 .specs/<id>/ 向上两级推导项目根目录

    specs_dir 结构为 <project>/.specs/<change-id>/，
    向上两级得到项目根目录。

    参数：
        specs_dir: .specs/<id>/ 的绝对或相对路径
    返回：
        项目根目录的绝对路径
    """
    return os.path.dirname(os.path.dirname(os.path.abspath(specs_dir)))


def resolve_skill_dir() -> str:
    """从 __file__ (references/scripts/) 推导 skill 根目录

    脚本位于 <skill-root>/references/scripts/xxx.py，
    向上两级 (scripts/ → references/ → skill-root)。

    返回：
        skill 根目录的绝对路径
    """
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(os.path.dirname(scripts_dir))  # references/scripts/ → skill root


def resolve_skill_dir_for_audit() -> str:
    """BITTER PILL 专用：多级查找 skill 根目录

    查找优先级：
    1. 从脚本自身位置推导（resolve_skill_dir）
    2. 从项目根目录查找 SKILL.md
    3. 从 FLOWGO_SKILL_DIR 环境变量

    每级查找都验证目标目录包含 SKILL.md。

    返回：
        skill 根目录的绝对路径
    """
    # 1. 从脚本位置推导
    local = resolve_skill_dir()
    if (Path(local) / "SKILL.md").exists():
        return local

    # 2. 从 CWD 向上查找项目根（包含 .specs/ 或 SKILL.md 的目录）
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / "SKILL.md").exists():
            return str(parent)
        if (parent / ".specs").is_dir():
            # 项目根可能不是 skill 根，但 SKILL.md 可能在项目根
            if (parent / "SKILL.md").exists():
                return str(parent)

    # 3. 环境变量
    env_val = os.environ.get("FLOWGO_SKILL_DIR")
    if env_val and Path(env_val).exists() and (Path(env_val) / "SKILL.md").exists():
        return env_val

    # 回退到脚本位置推导（即使 SKILL.md 不存在，也比报错好）
    return local


def resolve_history_path(specs_dir: str = None) -> str:
    """推导 health-history.jsonl 路径

    优先级：
    1. --specs-dir 推导（.specs/<id>/ → 项目根目录）
    2. FLOWGO_HISTORY 环境变量
    3. health-history.jsonl（CWD 相对）+ 警告

    参数：
        specs_dir: .specs/<id>/ 路径（可选）
    返回：
        health-history.jsonl 的路径
    """
    if specs_dir:
        project_root = resolve_project_root(specs_dir)
        return os.path.join(project_root, "health-history.jsonl")

    env_val = os.environ.get("FLOWGO_HISTORY")
    if env_val:
        return env_val

    print(
        f"⚠️ 未指定路径参数，health-history.jsonl 写到 CWD：{os.getcwd()}",
        file=sys.stderr,
    )
    return "health-history.jsonl"
