# TASK — fix-dev-gate-bypass

## 任务总览

| id | name | type | mode | depends_on | priority |
|----|------|------|------|-----------|----------|
| T01 | 修复测试绕过（3-develop.md + anti-patterns.md） | bugfix | afk | 无 | Must |
| T02 | 修复开发完成门禁（gate_artifacts.py + gate_check.py） | bugfix | afk | 无 | Must |

## 依赖图

```
T01 [P]──┐
         ├──→ 提交
T02 [P]──┘
```

T01 和 T02 无依赖，可并行执行。

---

## T01: 修复测试绕过

```xml
<task id="T01" type="bugfix" mode="afk" priority="Must">
  <name>修复测试绕过（3-develop.md + anti-patterns.md）</name>
  <read_files>
    references/stages/3-develop.md
    references/anti-patterns.md
  </read_files>
  <write_files>
    references/stages/3-develop.md
    references/anti-patterns.md
  </write_files>
  <action>
    1. 编辑 references/stages/3-develop.md：
       - 步骤 3：将"前置健康检查（可选）"改为"前置健康检查"，将"如有失败先记录为'已有问题'"改为"任何失败必须先修复再继续开发——不区分'是否本次变更导致'，全部视为阻塞项"
       - 步骤 9：将"跑 verify：贴出真实命令输出，未通过不标记完成"改为"跑 verify：贴出真实命令输出。verify 必须全部通过（0 失败）——不区分失败来源，任何测试失败都是阻塞项，禁止以'不是本次变更导致'为由绕过。未通过不标记完成"
       - 完成条件：将"verify 通过 + 交叉评审 6 维全 PASS + SUMMARY 完成"改为"verify 通过（0 失败） + 交叉评审 6 维全 PASS + SUMMARY 完成 + 代码已提交"
    2. 编辑 references/anti-patterns.md：
       - 在 3-开发 反模式表格末尾追加 dev-06 和 dev-07 两条目
  </action>
  <verify>grep -c "已有问题" references/stages/3-develop.md | grep -q "^0$" &amp;&amp; grep -q "0 失败" references/stages/3-develop.md &amp;&amp; grep -q "代码已提交" references/stages/3-develop.md &amp;&amp; grep -q "dev-06" references/anti-patterns.md &amp;&amp; grep -q "dev-07" references/anti-patterns.md &amp;&amp; echo "T01 verify PASS"</verify>
  <done>步骤 3 不含"已有问题"、步骤 9 含"0 失败"、完成条件含"代码已提交"、anti-patterns 含 dev-06 和 dev-07</done>
  <depends_on>无</depends_on>
  <e2e_coverage>stage-definition → anti-pattern</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>纯文本编辑任务，无需代码执行。2 个文件各改 3-4 处。</agent_hint>
</task>
```

## T02: 修复开发完成门禁

```xml
<task id="T02" type="bugfix" mode="afk" priority="Must">
  <name>修复开发完成门禁（gate_artifacts.py + gate_check.py）</name>
  <read_files>
    references/scripts/gate_artifacts.py
    references/scripts/gate_check.py
  </read_files>
  <write_files>
    references/scripts/gate_artifacts.py
    references/scripts/gate_check.py
  </write_files>
  <action>
    1. 编辑 references/scripts/gate_artifacts.py：
       - 顶部 import 增加 glob, subprocess
       - check_artifacts() 签名增加 project_dir=None 参数（向后兼容）
       - 在 return 前新增阶段 4 特殊检查：
         a) SUMMARY.md 检查：glob *.specs/<id>/*-SUMMARY.md，仅 complexity in (standard, heavy) 且 path_mode in (full, incremental)
         b) 代码已提交检查：subprocess.run(["git", "diff", "--name-only", "HEAD"], cwd=project_dir)，所有复杂度
         c) PROGRESS 残留检查：glob *.specs/<id>/*-PROGRESS.md，所有复杂度
       - subprocess 失败时 catch 异常，输出 warning 不阻塞
    2. 编辑 references/scripts/gate_check.py：
       - 将 check_artifacts(args.stage, specs_dir, args.complexity, args.path_mode) 改为 check_artifacts(args.stage, specs_dir, args.complexity, args.path_mode, project_dir=args.project_dir)
  </action>
  <verify>cd references/scripts &amp;&amp; python3 -c "from gate_artifacts import check_artifacts; import inspect; sig = inspect.signature(check_artifacts); assert 'project_dir' in sig.parameters, 'project_dir param missing'; print('T02 verify PASS')"</verify>
  <done>check_artifacts 有 project_dir 参数、阶段 4 检查 SUMMARY.md + git status + PROGRESS.md、gate_check.py 传递 project_dir</done>
  <depends_on>无</depends_on>
  <e2e_coverage>gate-script → gate-check-dispatcher</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>Python 代码修改任务。新增参数保持向后兼容（默认值 None）。subprocess 调用需要异常处理。</agent_hint>
</task>
```
