# TASK — skill-evolver-optimization

## 依赖图

```
T01 ──→ T05 ──→ T07 ──→ T09
  └───→ T06 ──↗     ↗
T02 ──────────→ T07
T03 ──→ T08 ──→ T09
T04（独立）
```

T01/T02/T03/T04 四个任务无依赖，可并行执行。

## 并行分组

- 组 A [并行]：T01(small) + T02(small) + T03(small) + T04(medium) — 基础模块创建，互不依赖
- 串行链 1：T05(medium) + T06(medium) — 门控核心模块，依赖 T01
- 串行链 2：T07(medium) — gate_check.py 重构，依赖 T01+T02+T05+T06
- 串行链 3：T08(small) — evolution_signal 扩展，依赖 T03
- 串行链 4：T09(small) — 阶段文件更新，依赖 T07+T08

## 任务列表

<task id="T01" parallel="true" priority="must" type="refactor">
  <name>基础模块提取（gate_dimensions + gate_artifacts + gate_blast）</name>
  <read_files>
    references/scripts/gate_check.py
  </read_files>
  <write_files>
    references/scripts/gate_dimensions.py
    references/scripts/gate_artifacts.py
    references/scripts/gate_blast.py
  </write_files>
  <action>
从 gate_check.py 提取三个基础模块：
1. gate_dimensions.py：提取 DANGEROUS_PATTERNS 常量 + 新增 EFFICIENCY_THRESHOLD = 0.5 常量。约 30 行。
2. gate_artifacts.py：提取 check_artifacts() 函数 + STANDARD_GATES/LITE_GATES/HEAVY_GATES 字典。约 60 行。
3. gate_blast.py：提取 check_blast_radius() 函数。约 50 行。
每个模块文件头部保留 #!/usr/bin/env python3 和模块 docstring。gate_check.py 暂不修改（T07 统一重构）。
  </action>
  <verify>cd /home/cgh/.claude/skills/flow-go && python3 -c "
import sys; sys.path.insert(0,'references/scripts')
from gate_dimensions import DANGEROUS_PATTERNS, EFFICIENCY_THRESHOLD
from gate_artifacts import check_artifacts, STANDARD_GATES
from gate_blast import check_blast_radius
assert len(DANGEROUS_PATTERNS) > 0, 'DANGEROUS_PATTERNS 为空'
assert EFFICIENCY_THRESHOLD > 0, 'EFFICIENCY_THRESHOLD 无效'
assert 0 in STANDARD_GATES, 'STANDARD_GATES 缺少 stage 0'
r = check_blast_radius('.', threshold=10)
assert 'file_count' in r, 'blast_radius 缺少 file_count'
print('T01 PASS: 3 个基础模块可导入且导出正确')
"</verify>
  <done>三个基础模块文件已创建，可独立导入，常量和函数行为与原 gate_check.py 一致</done>
  <depends_on></depends_on>
  <context_budget>small</context_budget>
  <agent_hint>纯提取，不改逻辑，可与其他 small 任务并行</agent_hint>
</task>

<task id="T02" parallel="true" priority="must" type="feature">
  <name>L3 跨 Change 回归检查（gate_l3.py）</name>
  <read_files>
    references/scripts/gate_check.py
    .specs/skill-evolver-optimization/DESIGN.md
  </read_files>
  <write_files>
    references/scripts/gate_l3.py
  </write_files>
  <action>
新建 gate_l3.py，实现 L3 条件触发的跨 Change 回归检查：
- check(specs_dir, traces_path) 函数
- 读 traces.jsonl 最后 3 条记录
- 比对每条记录的 gate_blocks 字段，检测是否有新的阻断维度
- JSON 解析失败 → 返回 {passed: true, detail: "trace 解析失败，跳过 L3"}（不阻断）
- traces.jsonl 不存在 → 返回 {passed: true, detail: "traces.jsonl 不存在，跳过 L3"}
约 60 行，纯 Python stdlib（json, pathlib）。
  </action>
  <verify>cd /home/cgh/.claude/skills/flow-go && python3 -c "
import sys; sys.path.insert(0,'references/scripts')
from gate_l3 import check
# traces 不存在时应返回 passed=true
r = check('.specs/skill-evolver-optimization', '/nonexistent/traces.jsonl')
assert r['passed'] == True, f'traces 不存在时应 passed=true, got {r}'
print('T02 PASS: gate_l3 可导入，traces 不存在时正确跳过')
"</verify>
  <done>gate_l3.py 已创建，check() 函数可被导入，traces 不存在时优雅跳过</done>
  <depends_on></depends_on>
  <context_budget>small</context_budget>
  <agent_hint>独立新模块，无依赖。参考 DESIGN.md ADR-003 设计</agent_hint>
</task>

<task id="T03" parallel="true" priority="must" type="feature">
  <name>LESSONS.md 追加模块（lessons_writer.py）</name>
  <read_files>
    references/scripts/evolution_signal.py
    .specs/skill-evolver-optimization/DESIGN.md
  </read_files>
  <write_files>
    references/scripts/lessons_writer.py
  </write_files>
  <action>
新建 lessons_writer.py，实现信号写入 LESSONS.md：
- write(signals_payload, lessons_path) 函数
- 输入：signals_payload（evolution_signal.py detect() 的输出 JSON）和 lessons_path（LESSONS.md 路径）
- 两层处理：
  1. 文件不存在 → 创建文件并写入基础模板（含 "## 待改进领域" 章节）
  2. 文件存在但无 "## 待改进领域" 章节 → 追加章节标题
- 将 strong_signals 格式化为表格行追加到 "## 待改进领域" 下：| 归因标签 | 信号描述 | 改进建议 |
- 返回 {written: true, count: N}
约 50 行。使用 pathlib + 原子写入（tmp + os.replace）。
  </action>
  <verify>cd /home/cgh/.claude/skills/flow-go && python3 -c "
import sys, tempfile, os; sys.path.insert(0,'references/scripts')
from lessons_writer import write
# 测试文件不存在场景
with tempfile.TemporaryDirectory() as td:
    path = os.path.join(td, 'LESSONS.md')
    payload = {'strong_signals': [{'attribution': '🔴 验证不足', 'description': '测试信号', 'advice': '增加自检'}], 'medium_signals': []}
    r = write(payload, path)
    assert r['written'] == True, f'写入失败: {r}'
    assert os.path.isfile(path), 'LESSONS.md 未创建'
    content = open(path).read()
    assert '## 待改进领域' in content, '缺少待改进领域章节'
    assert '🔴 验证不足' in content, '信号内容未写入'
    print('T03 PASS: lessons_writer 文件不存在时创建+写入正确')
"</verify>
  <done>lessons_writer.py 已创建，write() 函数可处理文件不存在和章节不存在两种场景</done>
  <depends_on></depends_on>
  <context_budget>small</context_budget>
  <agent_hint>独立新模块，参考 DESIGN.md ADR-004 表格格式</agent_hint>
</task>

<task id="T04" parallel="true" priority="must" type="feature">
  <name>evolution_reflect.py 优先级路由扩展</name>
  <read_files>
    references/scripts/evolution_reflect.py
    .specs/skill-evolver-optimization/DESIGN.md
  </read_files>
  <write_files>
    references/scripts/evolution_reflect.py
  </write_files>
  <action>
在现有 evolution_reflect.py 中扩展 reflect() 函数输出，新增 priority_ranking 字段：

1. 新增 PRIORITY_LEVELS 字典（6 级定义 + 映射条件）：
   - P1 修崩溃：gate_blocked/hotfix_trigger + 归因频率≥2
   - P2 利用成功：CAPTURE 策略 + 健康评分≥8.5
   - P3 攻克持久失败：signature 历史≥3次
   - P4 探索新方向：新信号类型 / P1-P3 无 evidence 降级
   - P5 简化：blast_radius/similar_error + 频率=1
   - P6 激进变异：用户显式要求，无历史数据

2. 新增 _rank_hypotheses(hypotheses, history_records) 函数：
   - 遍历每个 hypothesis，根据信号类型 + 归因频率分配优先级
   - P1-P3 条目必须有 trace_evidence（从 traces.jsonl 或 PROGRESS.md 提取）
   - 无 trace_evidence → 降级到 P4，标注 demoted=true + demoted_from

3. 修改 reflect() 返回值：新增 priority_ranking 字段（按 P1→P6 排序的列表）

不改变现有 reflect() 的核心逻辑（假设生成、去重、顿悟机制），仅扩展输出。
  </action>
  <verify>cd /home/cgh/.claude/skills/flow-go && python3 -c "
import sys; sys.path.insert(0,'references/scripts')
from evolution_reflect import reflect
signals = {'change_id': 'test', 'date': '2026-01-01', 'strong_signals': [{'type': 'gate_blocked', 'level': 'strong', 'description': '闸门阻断', 'evidence': ['stage 3 blocked'], 'attribution': '🟠 过度谨慎', 'reason': '前置条件过严', 'advice': '检查闸门条件'}], 'medium_signals': []}
r = reflect(signals)
assert 'priority_ranking' in r, f'缺少 priority_ranking 字段: {list(r.keys())}'
assert len(r['priority_ranking']) > 0, 'priority_ranking 为空'
for item in r['priority_ranking']:
    assert 'priority' in item, f'条目缺少 priority: {item}'
    assert 'trace_evidence' in item, f'条目缺少 trace_evidence: {item}'
print(f'T04 PASS: priority_ranking 有 {len(r[\"priority_ranking\"])} 条，优先级分配正确')
"</verify>
  <done>evolution_reflect.py reflect() 输出包含 priority_ranking 字段，按 6 级优先级排序，P1-P3 有 trace_evidence</done>
  <depends_on></depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>在现有文件上扩展，不改变核心逻辑。参考 DESIGN.md 优先级映射规则表</agent_hint>
</task>

<task id="T05" parallel="false" priority="must" type="feature">
  <name>L1 快速门卫（gate_l1.py）</name>
  <read_files>
    references/scripts/gate_check.py
    references/scripts/gate_dimensions.py
    references/scripts/gate_blast.py
    .specs/skill-evolver-optimization/DESIGN.md
  </read_files>
  <write_files>
    references/scripts/gate_l1.py
  </write_files>
  <action>
新建 gate_l1.py，实现 L1 快速门卫模式（AC-4）：

- check(specs_dir, project_dir) 函数
- 三路检查 AND 逻辑：
  1. security：从 gate_dimensions 导入 DANGEROUS_PATTERNS，扫描 specs 目录 .md 文件
  2. blast：从 gate_blast 导入 check_blast_radius
  3. structure：检查 SKILL.md 基本结构（文件存在 + 关键章节标题）
- 返回 {passed, dimensions: {security, blast, structure}}
- 目标：< 5 秒返回（纯文件扫描 + git diff，无复杂计算）
约 70 行。
  </action>
  <verify>cd /home/cgh/.claude/skills/flow-go && python3 -c "
import sys; sys.path.insert(0,'references/scripts')
from gate_l1 import check
r = check('.specs/skill-evolver-optimization', '.')
assert 'passed' in r, f'缺少 passed 字段: {r}'
assert 'dimensions' in r, '缺少 dimensions 字段'
dims = r['dimensions']
assert 'security' in dims, '缺少 security 维度'
assert 'blast' in dims, '缺少 blast 维度'
assert 'structure' in dims, '缺少 structure 维度'
print(f'T05 PASS: gate_l1 check() returned passed={r[\"passed\"]}, 3 维齐全')
"</verify>
  <done>gate_l1.py 已创建，check() 函数返回 3 维 AND 结果，秒级响应</done>
  <depends_on>T01</depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>依赖 T01 的 gate_dimensions.py 和 gate_blast.py。参考 DESIGN.md L1 数据流</agent_hint>
</task>

<task id="T06" parallel="false" priority="must" type="feature">
  <name>L2 全量 5 维评测（gate_l2.py）</name>
  <read_files>
    references/scripts/gate_check.py
    references/scripts/gate_dimensions.py
    .specs/skill-evolver-optimization/DESIGN.md
  </read_files>
  <write_files>
    references/scripts/gate_l2.py
  </write_files>
  <action>
新建 gate_l2.py，实现 L2 全量 5 维 AND 门控（AC-1/2/3）：

- check(specs_dir, project_dir) 函数
- 5 维检查（前 4 维从 gate_check.py 提取，第 5 维新增）：
  1. quality：从 *-SUMMARY.md 提取 verify 通过率 ≥ 80%
  2. scope：TASK.md write_files vs git diff --name-only
  3. security：DANGEROUS_PATTERNS 扫描
  4. regression：TEST.md 回归关键词检查
  5. efficiency（新增）：_efficiency(specs_dir, project_dir) 子函数
     - 从 TEST.md 或 *-SUMMARY.md 提取 AC 通过数
     - git diff --stat 提取总 +lines
     - ratio = ac_passed / (lines/100)
     - ratio ≥ EFFICIENCY_THRESHOLD → passed
     - git diff 无改动 → passed=true（纯文档变更）
- 返回 {passed, dimensions: {quality, scope, security, regression, efficiency}}
约 130 行。
  </action>
  <verify>cd /home/cgh/.claude/skills/flow-go && python3 -c "
import sys; sys.path.insert(0,'references/scripts')
from gate_l2 import check
r = check('.specs/skill-evolver-optimization', '.')
assert 'passed' in r, f'缺少 passed: {r}'
dims = r['dimensions']
assert len(dims) == 5, f'期望 5 维, got {len(dims)}: {list(dims.keys())}'
assert 'efficiency' in dims, '缺少 efficiency 维度'
print(f'T06 PASS: gate_l2 5 维齐全, passed={r[\"passed\"]}')
"</verify>
  <done>gate_l2.py 已创建，5 维 AND 门控含新增 efficiency 维度，AC-1/2/3 满足</done>
  <depends_on>T01</depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>依赖 T01 的 gate_dimensions.py。核心任务是第 5 维 efficiency 的实现。参考 DESIGN.md ADR-002</agent_hint>
</task>

<task id="T07" parallel="false" priority="must" type="refactor">
  <name>gate_check.py 瘦身为 CLI 调度器</name>
  <read_files>
    references/scripts/gate_check.py
    references/scripts/gate_artifacts.py
    references/scripts/gate_blast.py
    references/scripts/gate_l1.py
    references/scripts/gate_l2.py
    references/scripts/gate_l3.py
  </read_files>
  <write_files>
    references/scripts/gate_check.py
  </write_files>
  <action>
将 gate_check.py 重构为瘦 CLI 调度器（≤80 行）：

1. 保留 argparse CLI 入口，新增 --mode l1-guard 和 --enable-l3 参数
2. 删除已提取到子模块的函数体（check_artifacts → gate_artifacts, check_blast_radius → gate_blast, 4 个 _check_*_dimension → gate_l2, DANGEROUS_PATTERNS → gate_dimensions）
3. 保留 check_artifacts(), check_blast_radius(), check_quality_gate() 函数签名作为委托入口（向后兼容）：
   - check_artifacts → from gate_artifacts import check_artifacts (直接 re-export)
   - check_blast_radius → from gate_blast import check_blast_radius
   - check_quality_gate → from gate_l2 import check; 委托调用
4. main() 中根据 --mode 分发：
   - l1-guard → gate_l1.check()
   - quality-gate → gate_l2.check() [+ gate_l3.check() if --enable-l3]
   - blast-radius → gate_blast.check_blast_radius()
   - 无 mode → gate_artifacts.check_artifacts()
5. 目标 ≤ 80 行（argparse 定义 + 委托调用 + re-export）
  </action>
  <verify>cd /home/cgh/.claude/skills/flow-go && python3 references/scripts/gate_check.py --mode l1-guard --specs-dir .specs/skill-evolver-optimization --project-dir . 2>&1 && python3 references/scripts/gate_check.py --mode quality-gate --specs-dir .specs/skill-evolver-optimization --project-dir . 2>&1 && python3 -c "
import sys; sys.path.insert(0,'references/scripts')
# 向后兼容：原函数签名仍可用
from gate_check import check_artifacts, check_blast_radius, check_quality_gate
r = check_artifacts(3, '.specs/skill-evolver-optimization')
assert 'passed' in r, f'check_artifacts 向后兼容失败: {r}'
print('T07 PASS: gate_check.py CLI 3 模式可用 + 原函数签名向后兼容')
"</verify>
  <done>gate_check.py 重构为 ≤80 行调度器，3 种 --mode 均可用，原函数签名向后兼容</done>
  <depends_on>T01,T02,T05,T06</depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>确保向后兼容是关键。原 check_artifacts/check_blast_radius/check_quality_gate 签名必须保留</agent_hint>
</task>

<task id="T08" parallel="false" priority="must" type="feature">
  <name>evolution_signal.py --write-lessons 扩展</name>
  <read_files>
    references/scripts/evolution_signal.py
    references/scripts/lessons_writer.py
  </read_files>
  <write_files>
    references/scripts/evolution_signal.py
  </write_files>
  <action>
在现有 evolution_signal.py 中扩展 CLI，新增 --write-lessons 参数（AC-6）：

1. argparse 新增 --write-lessons flag（store_true）
2. main() 中，当 --write-lessons 且 result 包含 strong_signals 时：
   - from lessons_writer import write
   - 确定 LESSONS.md 路径：specs_dir 的上级目录 / LESSONS.md
   - 调用 write(result, lessons_path)
   - 输出写入结果到 stderr
3. --write-lessons 但无 strong_signals → 输出 "无强信号，跳过 LESSONS 写入" 到 stderr
4. 不改变 detect() 核心逻辑
  </action>
  <verify>cd /home/cgh/.claude/skills/flow-go && python3 references/scripts/evolution_signal.py --specs-dir .specs/skill-evolver-optimization --write-lessons 2>&1 && python3 -c "
import sys; sys.path.insert(0,'references/scripts')
# 验证 --write-lessons 参数已注册
import subprocess
r = subprocess.run(['python3', 'references/scripts/evolution_signal.py', '--help'], capture_output=True, text=True)
assert '--write-lessons' in r.stdout, '--write-lessons 参数未注册'
print('T08 PASS: --write-lessons 参数可用')
"</verify>
  <done>evolution_signal.py 支持 --write-lessons 参数，信号自动格式化写入 LESSONS.md</done>
  <depends_on>T03</depends_on>
  <context_budget>small</context_budget>
  <agent_hint>小改动：argparse 加一个 flag + main() 加一个 if 分支</agent_hint>
</task>

<task id="T09" parallel="false" priority="must" type="doc">
  <name>3-develop.md + special-flows.md 阶段文件更新</name>
  <read_files>
    references/stages/3-develop.md
    references/stages/special-flows.md
  </read_files>
  <write_files>
    references/stages/3-develop.md
    references/stages/special-flows.md
  </write_files>
  <action>
在两个阶段文件中新增 LESSONS 闭环相关步骤：

1. 3-develop.md 新增（AC-7 + AC-8）：
   - 在开发阶段步骤开头新增"前置提醒"步骤：自动 grep .specs/LESSONS.md 中与当前 change 类型匹配的"待改进领域"条目，输出前置提醒
   - 新增 auto-verify 可选步骤：读取 .flowgo-config 中 auto_verify 配置（默认 false），若 true 则每完成子任务自动运行 `python3 references/scripts/gate_check.py --mode l1-guard --specs-dir .specs/<id> --project-dir .`，失败则输出失败项 + 建议运行 `git stash`

2. special-flows.md 归档流程中新增（AC-6 触发点）：
   - 在归档流程的进化分析步骤后，新增 `python3 references/scripts/evolution_signal.py --specs-dir .specs/<id> --write-lessons` 调用步骤

不改现有步骤的顺序和内容，仅插入新步骤。
  </action>
  <verify>cd /home/cgh/.claude/skills/flow-go && grep -c "LESSONS" references/stages/3-develop.md && grep -c "auto.verify\|auto_verify" references/stages/3-develop.md && grep -c "write-lessons" references/stages/special-flows.md && echo "T09 PASS: 3-develop.md 含 LESSONS+auto_verify, special-flows.md 含 --write-lessons"</verify>
  <done>3-develop.md 含 LESSONS 前置提醒 + auto-verify 步骤；special-flows.md 归档流程含 --write-lessons 调用</done>
  <depends_on>T07,T08</depends_on>
  <context_budget>small</context_budget>
  <agent_hint>纯文档更新，不改代码。在现有步骤间插入新步骤</agent_hint>
</task>
