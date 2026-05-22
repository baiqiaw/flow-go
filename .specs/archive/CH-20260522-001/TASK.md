# TASK — CH-20260522-001

## 依赖图
T01 → T03（SKILL.md 引用 gate-rules.md，需先创建）
T01 → T04（gate_check.py 分类需对齐 gate-rules.md 规则分类）
T02 独立（anti-patterns.md 原子化，不依赖其他任务）
T05 独立（进化机制注入，不依赖其他任务）
T01 + T02 + T05 可并行 → T03 → T04

## 并行分组
- 组 A [并行]：T01(small) + T02(small) + T05(small) — 无依赖，可同时执行
- 串行：T03(small) → 依赖组 A(T01)
- 串行：T04(small) → 依赖组 A(T01)

## 任务列表

<task id="T01" parallel="true" priority="must" type="refactor" mode="afk">
  <name>创建 gate-rules.md 外置闸门+角色约束</name>
  <read_files>/home/cgh/.claude/skills/flow-go/SKILL.md</read_files>
  <write_files>/home/cgh/.claude/skills/flow-go/references/gate-rules.md</write_files>
  <action>从 SKILL.md 提取闸门检查表（第四步闸门检查的表格部分，约第 235-250 行区间）和角色约束速查表（约第 287-296 行区间）到新文件 references/gate-rules.md。文件分为 3 个章节：1) 闸门检查规则（含分类标签 gate/role/safety）2) 角色约束规则 3) HARD-GATE 原则声明。每条规则添加分类标签用于 --categories 过滤。</action>
  <verify>test -f /home/cgh/.claude/skills/flow-go/references/gate-rules.md && grep -c "gate\|role\|safety" /home/cgh/.claude/skills/flow-go/references/gate-rules.md | head -1</verify>
  <done>gate-rules.md 存在且包含闸门检查表+角色约束表+分类标签，对应 AC-1</done>
  <depends_on></depends_on>
  <e2e_coverage>SKILL.md 提取 → gate-rules.md 创建 → 内容完整</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>纯文件创建，可独立执行</agent_hint>
</task>

<task id="T02" parallel="true" priority="must" type="refactor" mode="afk">
  <name>anti-patterns.md 添加原子化 id 字段</name>
  <read_files>/home/cgh/.claude/skills/flow-go/references/anti-patterns.md</read_files>
  <write_files>/home/cgh/.claude/skills/flow-go/references/anti-patterns.md</write_files>
  <action>为 anti-patterns.md 每个阶段的每条反模式添加唯一 id 字段。格式：`阶段-序号-关键词`（如 `req-01-solution-as-requirement`）。在每行表格的 Anti-Pattern 列前插入 `[id]` 标记。保留原有三列结构不变。</action>
  <verify>grep -c "\[.*-.*-\]" /home/cgh/.claude/skills/flow-go/references/anti-patterns.md</verify>
  <done>每条反模式有唯一 id，格式统一，可被 grep 逐条检查，对应 AC-2</done>
  <depends_on></depends_on>
  <e2e_coverage>读取 anti-patterns.md → 添加 id → 验证格式</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>纯文本修改，可独立执行</agent_hint>
</task>

<task id="T03" parallel="false" priority="must" type="refactor" mode="afk">
  <name>SKILL.md 内联内容替换为 grep 引用</name>
  <read_files>/home/cgh/.claude/skills/flow-go/SKILL.md</read_files>
  <write_files>/home/cgh/.claude/skills/flow-go/SKILL.md</write_files>
  <action>将 SKILL.md 中闸门检查表和角色约束速查表的完整内联内容替换为 grep 加载引用。保留 HARD-GATE 原则声明和 LITE 不可跳过场景（这些是核心流程逻辑）。替换格式：`> 闸门检查规则和角色约束见 references/gate-rules.md（grep 对应阶段加载）`。验证替换后 SKILL.md 减少 ≥30 行。当前基线：481 行。</action>
  <verify>test $(wc -l < /home/cgh/.claude/skills/flow-go/SKILL.md) -le 451</verify>
  <done>SKILL.md 减少 ≥30 行，闸门和角色内容通过引用加载，对应 AC-1 验收线</done>
  <depends_on>T01</depends_on>
  <e2e_coverage>SKILL.md 修改 → 行数减少验证 → 引用格式正确</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>依赖 T01 完成</agent_hint>
</task>

<task id="T04" parallel="false" priority="must" type="feature" mode="afk">
  <name>gate_check.py 添加 --categories 参数 + 结构化输出</name>
  <read_files>/home/cgh/.claude/skills/flow-go/references/scripts/gate_check.py</read_files>
  <write_files>/home/cgh/.claude/skills/flow-go/references/scripts/gate_check.py</write_files>
  <action>两项改动：(1) 在 argparse 中添加 --categories 可选参数（逗号分隔），类别包括：gate（闸门前置）、antipattern（反模式）、role（角色约束）、safety（安全场景）。不传时行为与现有一致。类别与 gate-rules.md 分类标签对齐。(2) 添加 --structured-output 参数，启用后输出格式改为 `STAGE-N: artifact ✅ / artifact ❌ / artifact ⚠️`（每行一个工件），替代当前的 JSON 格式。不传时保持现有输出格式。</action>
  <verify>python3 /home/cgh/.claude/skills/flow-go/references/scripts/gate_check.py --help 2>&1 | grep -c "categories\|structured"</verify>
  <done>gate_check.py 支持 --categories 和 --structured-output 参数，对应 AC-3 + AC-4</done>
  <depends_on>T01</depends_on>
  <e2e_coverage>argparse 扩展 → 帮助信息验证 → 全量模式回归</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>依赖 T01 完成以对齐分类名称</agent_hint>
</task>

<task id="T05" parallel="true" priority="must" type="feature" mode="afk">
  <name>进化机制注入 5 项架构原则</name>
  <read_files>/home/cgh/.claude/skills/flow-go/references/scripts/evolution_reflect.py</read_files>
  <write_files>/home/cgh/.claude/skills/flow-go/references/scripts/evolution_reflect.py</write_files>
  <action>在 evolution_reflect.py 的 SUGGEST 模式中添加 5 项架构原则检测维度：1) 原子化规则（每条规则可独立检查）2) 结构化输出（key:value 格式）3) 关注点分离（编排vs知识）4) 单一职责（每个文件一个职责）5) 可组合规则（按类别选择性执行）。当 SUGGEST 模式运行时，扫描 SKILL.md 和 references/ 目录，检测违反这 5 项原则的内联规则或结构问题，生成改进建议。原则定义以常量字典形式添加到文件顶部。</action>
  <verify>python3 -c "import ast; ast.parse(open('/home/cgh/.claude/skills/flow-go/references/scripts/evolution_reflect.py').read()); print('OK')"</verify>
  <done>evolution_reflect.py 包含 5 项架构原则常量，SUGGEST 模式可检测违反项，对应 AC-5</done>
  <depends_on></depends_on>
  <e2e_coverage>常量添加 → SUGGEST 模式扩展 → 语法验证</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>独立于 T01-T04，可并行执行</agent_hint>
</task>
