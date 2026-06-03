"""flow-go skill 结构完整性验证器

检查 SKILL.md → stages → scripts → artifacts 的交叉引用一致性。
用于 pre-commit hook，确保 skill 结构变更不引入断裂引用。

用法：
    python3 validate_skill.py --skill-dir <path>
"""
import argparse
import ast
import json
import os
import re
import sys


def check_file_existence(skill_dir):
    """检查 SKILL.md 中引用的文件是否存在"""
    errors = []
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        return [{"check": "file_existence", "error": f"SKILL.md 不存在: {skill_dir}"}]

    with open(skill_md, encoding="utf-8") as f:
        content = f.read()

    # 匹配 references/ 下的文件引用
    refs = set(re.findall(r'references/[\w\-./]+\.(?:md|py)', content))

    # 匹配 stages/ 和 artifacts/ 引用
    refs.update(re.findall(r'references/(?:stages|artifacts)/[\w\-]+\.(?:md|py)', content))

    for ref in sorted(refs):
        full_path = os.path.join(skill_dir, ref)
        if not os.path.exists(full_path):
            errors.append({"check": "file_existence", "error": f"引用的文件不存在: {ref}"})

    return errors


def check_stage_coverage(skill_dir):
    """检查 8 个阶段 + special-flows 是否有对应文件"""
    errors = []
    stages_dir = os.path.join(skill_dir, "references", "stages")
    expected = [
        "0-requirement.md", "1-design.md", "2-task.md", "3-develop.md",
        "4-test.md", "5-review.md", "6-deploy.md", "7-acceptance.md",
        "special-flows.md",
    ]
    if not os.path.isdir(stages_dir):
        return [{"check": "stage_coverage", "error": f"stages 目录不存在: {stages_dir}"}]

    for stage_file in expected:
        if not os.path.isfile(os.path.join(stages_dir, stage_file)):
            errors.append({"check": "stage_coverage", "error": f"缺少阶段文件: references/stages/{stage_file}"})

    return errors


def check_script_params(skill_dir):
    """检查 SKILL.md/stages 中脚本调用的参数名是否与 argparse 定义一致"""
    errors = []
    scripts_dir = os.path.join(skill_dir, "references", "scripts")
    stages_path = os.path.join(skill_dir, "references", "stages")

    # 从 SKILL.md 和 stages/ 中提取脚本调用
    script_calls = []
    stage_files = []
    if os.path.isdir(stages_path):
        stage_files = [
            os.path.join(stages_path, f)
            for f in os.listdir(stages_path)
            if f.endswith(".md")
        ]

    for md_file in [os.path.join(skill_dir, "SKILL.md")] + stage_files:
        if not os.path.isfile(md_file):
            continue
        with open(md_file, encoding="utf-8") as f:
            for line in f:
                # 匹配 python3 references/scripts/xxx.py --param value
                m = re.findall(r'python3?\s+references/scripts/(\w+\.py)\s+((?:--[\w][\w-]*(?:\s+[^\s-][^\s]*)?\s*)+)', line)
                for script_name, params_str in m:
                    params = re.findall(r'(--[\w-]+)', params_str)
                    script_calls.append({"script": script_name, "params": set(params), "source": os.path.basename(md_file)})

    # 从脚本中提取 argparse 参数
    for call in script_calls:
        script_path = os.path.join(scripts_dir, call["script"])
        if not os.path.isfile(script_path):
            errors.append({"check": "script_params", "error": f"脚本不存在: {call['script']} (引用自 {call['source']})"})
            continue

        with open(script_path, encoding="utf-8") as f:
            source = f.read()

        # 提取 add_argument 调用中的参数名（支持多行定义）
        defined_params = set()
        for m in re.finditer(r'add_argument\(\s*["\'](--[\w-]+)', source, re.DOTALL):
            defined_params.add(m.group(1))

        # 检查引用的参数是否在 argparse 中定义
        for param in call["params"]:
            if param not in defined_params:
                errors.append({
                    "check": "script_params",
                    "error": f"{call['script']} 被引用时使用 {param}，但脚本 argparse 未定义 (引用自 {call['source']})",
                })

    return errors


def check_script_existence(skill_dir):
    """检查文档中按名称引用的所有脚本文件是否存在（含无参数调用）"""
    errors = []
    scripts_dir = os.path.join(skill_dir, "references", "scripts")

    # 扫描所有 md 文件中的脚本引用
    refs = set()
    for root, _, files in os.walk(skill_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                continue
            for m in re.finditer(r'references/scripts/(\w+\.py)', content):
                refs.add(m.group(1))

    for script_name in sorted(refs):
        if not os.path.isfile(os.path.join(scripts_dir, script_name)):
            errors.append({"check": "script_existence", "error": f"文档引用的脚本不存在: references/scripts/{script_name}"})

    return errors


def check_artifact_templates(skill_dir):
    """检查工件模板文件是否存在"""
    errors = []
    artifacts_dir = os.path.join(skill_dir, "references", "artifacts")
    expected = [
        "meta-artifacts.md", "spec-artifacts.md", "task-artifacts.md",
        "quality-artifacts.md", "deploy-artifacts.md",
    ]
    if not os.path.isdir(artifacts_dir):
        return [{"check": "artifact_templates", "error": f"artifacts 目录不存在: {artifacts_dir}"}]

    for artifact_file in expected:
        if not os.path.isfile(os.path.join(artifacts_dir, artifact_file)):
            errors.append({"check": "artifact_templates", "error": f"缺少工件模板: references/artifacts/{artifact_file}"})

    return errors


def check_critical_instructions(skill_dir):
    """检查关键指令结构元素是否存在（防止指令性回归）

    验证 SKILL.md 和阶段文件中包含防止 worktree 跳过和闸门检查跳过的
    关键结构元素。这些检查很轻量，quick 模式也执行。
    """
    errors = []

    # 1. 0-requirement.md 步骤 3.5 应有 HARD-GATE 标记和"禁止跳过"
    req_path = os.path.join(skill_dir, "references", "stages", "0-requirement.md")
    if os.path.isfile(req_path):
        with open(req_path, encoding="utf-8") as f:
            content = f.read()
        # 查找步骤 3.5 区域
        m = re.search(r'3\.5\s+\*\*(.+?)\*\*', content)
        if not m:
            errors.append({"check": "critical_instructions",
                           "error": "0-requirement.md 步骤 3.5 缺少标题（可能被删除或重编号）"})
        else:
            title = m.group(1)
            if "<HARD-GATE>" not in title:
                errors.append({"check": "critical_instructions",
                               "error": "0-requirement.md 步骤 3.5 缺少 <HARD-GATE> 标记（worktree 创建可能被跳过）"})
            if "禁止跳过" not in content[m.start():m.start() + 200]:
                errors.append({"check": "critical_instructions",
                               "error": "0-requirement.md 步骤 3.5 缺少 '禁止跳过' 文本"})
    else:
        errors.append({"check": "critical_instructions",
                       "error": "references/stages/0-requirement.md 不存在"})

    # 2. SKILL.md 第五步 · 角色声明应有闸门检查前置条件
    skill_path = os.path.join(skill_dir, "SKILL.md")
    if os.path.isfile(skill_path):
        with open(skill_path, encoding="utf-8") as f:
            skill_content = f.read()

        # 找第五步区域
        step5_match = re.search(r'##\s*第五步.*?角色声明', skill_content)
        if step5_match:
            # 取第五步到第六步之间的内容
            step5_start = step5_match.start()
            step6_match = re.search(r'##\s*第六步', skill_content[step5_start:])
            step5_section = skill_content[step5_start:step5_start + step6_match.start()] if step6_match else skill_content[step5_start:]
            if "闸门检查" not in step5_section or ("禁止输出角色声明" not in step5_section and "前置条件" not in step5_section):
                errors.append({"check": "critical_instructions",
                               "error": "SKILL.md 第五步 · 角色声明缺少闸门检查前置条件（闸门检查可能被跳过）"})
        else:
            errors.append({"check": "critical_instructions",
                           "error": "SKILL.md 缺少第五步 · 角色声明章节"})

        # 3. SKILL.md 自检部分应有"闸门检查已实际执行"
        self_check_match = re.search(r'##\s*自检', skill_content)
        if self_check_match:
            sc_start = self_check_match.start()
            # 取到下一个 ## 标题或文件末尾
            next_section = re.search(r'\n## ', skill_content[sc_start + 10:])
            sc_section = skill_content[sc_start:sc_start + 10 + next_section.start()] if next_section else skill_content[sc_start:]
            if "闸门检查已实际执行" not in sc_section:
                errors.append({"check": "critical_instructions",
                               "error": "SKILL.md 自检部分缺少 '闸门检查已实际执行'（闸门检查可能被跳过）"})
        else:
            errors.append({"check": "critical_instructions",
                           "error": "SKILL.md 缺少自检章节"})

        # 4. SKILL.md "Worktree 进入" 应有异常阻断（"停住"或"不继续"）
        wt_match = re.search(r'###\s*Worktree\s*进入', skill_content)
        if wt_match:
            wt_start = wt_match.start()
            next_h3 = re.search(r'\n## ', skill_content[wt_start + 5:])
            wt_section = skill_content[wt_start:wt_start + 5 + next_h3.start()] if next_h3 else skill_content[wt_start:]
            if "停住" not in wt_section and "不继续" not in wt_section:
                errors.append({"check": "critical_instructions",
                               "error": "SKILL.md 'Worktree 进入' 缺少异常阻断指令（worktree 异常时可能继续执行）"})
        else:
            errors.append({"check": "critical_instructions",
                           "error": "SKILL.md 缺少 'Worktree 进入' 章节"})

    return errors


def validate(skill_dir, quick=False):
    """执行全部检查，返回结果

    参数：
        skill_dir: skill 根目录
        quick: True 时跳过脚本参数交叉验证和脚本存在性检查（用于运行时快速健康检查）
    """
    all_errors = []
    all_errors.extend(check_file_existence(skill_dir))
    all_errors.extend(check_stage_coverage(skill_dir))
    all_errors.extend(check_critical_instructions(skill_dir))
    if not quick:
        all_errors.extend(check_script_params(skill_dir))
        all_errors.extend(check_script_existence(skill_dir))
    all_errors.extend(check_artifact_templates(skill_dir))
    checks_run = 4 if quick else 6
    return {
        "passed": len(all_errors) == 0,
        "errors": all_errors,
        "checks": checks_run,
    }


def _reconfigure_streams():
    """Windows GBK 终端兼容：确保 stdout/stderr 能输出 Unicode 字符"""
    for _stream in (sys.stdout, sys.stderr):
        if hasattr(_stream, "reconfigure"):
            _stream.reconfigure(errors="replace")


def main():
    parser = argparse.ArgumentParser(description="flow-go skill 结构完整性验证器")
    parser.add_argument("--skill-dir", required=True, help="flow-go skill 根目录")
    parser.add_argument("--quick", action="store_true",
                        help="快速模式：仅检查文件存在性和阶段/工件覆盖，跳过脚本参数交叉验证")
    parser.add_argument("--json-only", action="store_true",
                        help="仅输出 JSON 到 stdout（人类可读文本输出到 stderr），供 safe_run.py 解析")
    args = parser.parse_args()

    _reconfigure_streams()
    result = validate(args.skill_dir, quick=args.quick)

    if args.json_only:
        # JSON-only 模式：人类文本 → stderr，JSON → stdout
        if result["passed"]:
            print(f"✅ skill 结构验证通过（{result['checks']} 项检查）", file=sys.stderr)
        else:
            print(f"❌ skill 结构验证失败（{len(result['errors'])} 个问题）:", file=sys.stderr)
            for e in result["errors"]:
                print(f"  [{e['check']}] {e['error']}", file=sys.stderr)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["passed"]:
            print(f"✅ skill 结构验证通过（{result['checks']} 项检查）")
        else:
            print(f"❌ skill 结构验证失败（{len(result['errors'])} 个问题）:")
            for e in result["errors"]:
                print(f"  [{e['check']}] {e['error']}")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
