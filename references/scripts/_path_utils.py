"""flow-go 脚本共享路径工具

统一路径推导逻辑，消除各脚本中重复且不一致的 __file__ / CWD 推导。
"""
import os
import sys


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
