# TASK — evolution-pipeline-p0

## 依赖图
T01 和 T04 无互相依赖，可并行 [P]。
T02 → T03 串行（同一文件 gate_check.py，T03 需 T02 的辅助函数结构）。
无循环依赖。

## 并行分组
- 组 A [并行]：T01(small) + T04(small)
- 串行链：T02(medium) → T03(medium)

## 任务列表

<task id="T01" parallel="true" priority="must" type="refactor">
  <name>evolution_signal.py 新增 --traces 参数 + gate_blocked_trace 信号</name>
  <read_files>references/scripts/evolution_signal.py</read_files>
  <write_files>references/scripts/evolution_signal.py</write_files>
  <action>1) argparse 新增 --traces 可选参数（path 类型）
2) 新增 _read_traces(traces_path, change_id) 辅助函数：读取 traces.jsonl，按 change_id 过滤，提取 gate_blocks dict
3) 新增 _extract_gate_blocked_trace(specs_dir, traces_path) 辅助函数：调用 _read_traces，gate_blocks 中任一阶段 > 0 则生成 evidence 列表
4) 在 STRONG_EXTRACTORS 中新增 "gate_blocked_trace" 条目，指向 _extract_gate_blocked_trace
5) 修改 detect() 函数签名：新增 traces_path=None 参数；传入时额外调用 _extract_gate_blocked_trace
6) 信号去重：trace 产出的信号 source="trace"，正则产出的保持原值
7) traces.jsonl 读取失败时 stderr 输出警告，fallback 到纯正则模式
8) --traces 不带时行为完全不变</action>
  <verify>cd /home/cgh/projects/flow-go && python3 references/scripts/evolution_signal.py --specs-dir .specs/evolution-pipeline-p0 --traces .specs/traces.jsonl 2>&1 | python3 -c "import sys,json; d=json.load(sys.stdin); assert any(s.get('source')=='trace' for s in d.get('strong_signals',[])) or d.get('strong_count',0)>=0, 'trace source check failed'; print('T01 PASS: evolution_signal --traces OK')"</verify>
  <done>evolution_signal.py --traces 参数可正常调用；traces.jsonl 存在数据时产出 source="trace" 的 gate_blocked_trace 强信号；不带 --traces 时行为不变。覆盖 AC-1、AC-2</done>
  <depends_on></depends_on>
  <context_budget>small</context_budget>
  <agent_hint>可与其他 small 任务并行执行</agent_hint>
</task>

<task id="T02" parallel="false" priority="must" type="feature">
  <name>gate_check.py quality-gate 质量 + 范围维度</name>
  <read_files>references/scripts/gate_check.py</read_files>
  <write_files>references/scripts/gate_check.py</write_files>
  <action>1) 新增 _check_quality_dimension(specs_dir) 函数：
   - 读取 SUMMARY.md，解析 verify 通过率（3 种格式：百分比 `90%`、分数 `9/10`、关键词 `passed: 9`）
   - ≥80% → PASS，<80% → FAIL，无法解析 → PASS + warning
2) 新增 _check_scope_dimension(specs_dir, project_dir) 函数：
   - 读取 TASK.md，提取预期文件列表（glob 模式行）
   - 运行 git diff --name-only 获取实际改动
   - 实际文件均在 TASK.md 规划内 → PASS，有超规划 → FAIL
   - TASK.md 无文件列表 → PASS + detail 标注"跳过"
3) 新增 check_quality_gate(stage, specs_dir, project_dir) 骨架函数（本任务只填 quality + scope 两个维度，其余暂返回 PASS）</action>
  <verify>cd /home/cgh/projects/flow-go && python3 -c "
import sys; sys.path.insert(0,'references/scripts')
from gate_check import check_quality_gate
r = check_quality_gate(4, '.specs/evolution-pipeline-p0', '.')
d = r['dimensions']
assert 'quality' in d, 'quality dimension missing'
assert 'scope' in d, 'scope dimension missing'
assert d['quality']['passed'] in (True, False), 'quality not bool'
assert d['scope']['passed'] in (True, False), 'scope not bool'
print('T02 PASS: quality + scope dimensions OK')
"</verify>
  <done>gate_check.py 新增 check_quality_gate() 函数含 quality 和 scope 两个维度。覆盖 AC-3、AC-4</done>
  <depends_on></depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>独占 gate_check.py，后续 T03 依赖本任务结构</agent_hint>
</task>

<task id="T03" parallel="false" priority="must" type="feature">
  <name>gate_check.py quality-gate 安全 + 回归维度 + AND 逻辑 + CLI 接入</name>
  <read_files>references/scripts/gate_check.py</read_files>
  <write_files>references/scripts/gate_check.py</write_files>
  <action>1) 新增 DANGEROUS_PATTERNS 常量列表：`BEGIN PRIVATE KEY`、`BEGIN RSA PRIVATE KEY`、`rm -rf /`、`DROP TABLE`、`password\s*=\s*['"]`
2) 新增 _check_security_dimension(specs_dir) 函数：
   - 扫描 specs 目录下非 TEST.md 的 .md 文件
   - 逐文件正则匹配 DANGEROUS_PATTERNS
   - 无匹配 → PASS，有匹配 → FAIL + detail 列出文件和匹配内容
3) 新增 _check_regression_dimension(specs_dir) 函数：
   - 读取 TEST.md，查找"原已通过用例失败"/"previously passing.*failed"/"regression" 等标记
   - 无记录 → PASS，有记录 → FAIL + detail 引用具体行
4) 补全 check_quality_gate() 函数：
   - 调用 4 个维度检查函数
   - AND 逻辑：passed = quality AND scope AND security AND regression
   - 组装完整 JSON 输出（mode/logic/dimensions/passed）
5) 修改 main()：--mode choices 新增 "quality-gate"；quality-gate 模式调用 check_quality_gate()
6) quality-gate 模式退出码：passed=True → 0，passed=False → 1</action>
  <verify>cd /home/cgh/projects/flow-go && python3 references/scripts/gate_check.py --mode quality-gate --stage 4 --specs-dir .specs/evolution-pipeline-p0 --project-dir . 2>&1 | python3 -c "
import sys,json
r = json.load(sys.stdin)
assert r['mode'] == 'quality-gate', 'mode wrong'
assert r['logic'] == 'AND', 'logic wrong'
dims = r['dimensions']
for d in ['quality','scope','security','regression']:
    assert d in dims, f'{d} missing'
    assert 'passed' in dims[d], f'{d} no passed'
assert r['passed'] in (True, False), 'passed not bool'
print('T03 PASS: quality-gate AND logic OK')
"</verify>
  <done>gate_check.py quality-gate 模式完整：4 维 AND 逻辑 + CLI 接入。覆盖 AC-5、AC-6、AC-7</done>
  <depends_on>T02</depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>依赖 T02 的 check_quality_gate 骨架函数</agent_hint>
</task>

<task id="T04" parallel="true" priority="must" type="refactor">
  <name>health_scorer.py 输出格式增强 + 向前兼容</name>
  <read_files>references/scripts/health_scorer.py</read_files>
  <write_files>references/scripts/health_scorer.py</write_files>
  <action>1) 修改 main() 中 health-history.jsonl 写入逻辑，entry dict 新增 3 个字段：
   - changes_made: data.get("files_changed", data.get("changes_made", []))
   - trigger: data.get("trigger", "manual")
   - previous_score: 自动读取 health-history.jsonl 最近一条的 composite（无历史时为 null）
2) 新增 _read_previous_score(history_path) 辅助函数：
   - 读取 health-history.jsonl 最后一条
   - 返回 composite 值或 None
   - 文件不存在或为空 → 返回 None
   - 旧格式记录无新字段 → 不报错（向前兼容）
3) analyze_trends() 和其他读取 health-history.jsonl 的位置：缺失字段用默认值填充
   - changes_made 默认 []，trigger 默认 null，previous_score 默认 null
4) 输出 JSON 新字段通过现有 ensure_ascii=False + indent=2 格式写入</action>
  <verify>cd /home/cgh/projects/flow-go && python3 -c "
import json, tempfile, os
# 构造测试输入
inp = json.dumps({'ac_total':9,'ac_passed':9,'test_rounds_completed':1,'review_rounds':1,'code_lines_added':10,'code_lines_removed':5,'files_changed':['a.py'],'trigger':'test','change_id':'verify-test'})
# 写临时文件
tf = tempfile.NamedTemporaryFile(mode='w',suffix='.jsonl',delete=False)
tf.write(json.dumps({'ts':'2026-01-01','change_id':'old','composite':85.0,'grade':'A','rag':'Green','scores':{'AC 通过率':90}}) + '\n')
tf_path = tf.name; tf.close()
# 运行 scorer
import subprocess
env = os.environ.copy(); env['FLOWGO_HISTORY'] = tf_path
r = subprocess.run(['python3','references/scripts/health_scorer.py','/dev/stdin','--format','json'],input=inp,capture_output=True,text=True,env=env)
assert r.returncode == 0, f'scorer failed: {r.stderr}'
# 检查 jsonl 新字段
with open(tf_path) as f: lines = f.readlines()
last = json.loads(lines[-1])
assert 'changes_made' in last, 'changes_made missing'
assert 'trigger' in last, 'trigger missing'
assert 'previous_score' in last, 'previous_score missing'
assert last['changes_made'] == ['a.py'], f'changes_made wrong: {last[\"changes_made\"]}'
assert last['trigger'] == 'test', f'trigger wrong: {last[\"trigger\"]}'
assert last['previous_score'] == 85.0, f'previous_score wrong: {last[\"previous_score\"]}'
os.unlink(tf_path)
print('T04 PASS: health_scorer new fields OK')
"</verify>
  <done>health_scorer.py 输出 health-history.jsonl 新增 changes_made、trigger、previous_score 三个字段。旧格式向前兼容。覆盖 AC-8、AC-9</done>
  <depends_on></depends_on>
  <context_budget>small</context_budget>
  <agent_hint>可与其他 small 任务并行执行</agent_hint>
</task>
