# TASK — simplifier-borrow

## 依赖图
```
T01 (角色约束表) → T02 (反模式目录) → T03 (增量闸门) → T04 (过度优化护栏) → T05 (精炼环) → T06 (验证闭环)
```
全串行：所有任务编辑同一文件 SKILL.md，避免冲突。按注入依赖关系排列，确保上游注入先于下游引用。

## 并行分组
- 串行链：T01 → T02 → T03 → T04 → T05 → T06（同一文件编辑，不可并行）

## 任务列表

<task id="T01" parallel="false" priority="must" type="config" mode="afk">
  <name>正向首要原则：角色约束表扩展为双列</name>
  <read_files>SKILL.md</read_files>
  <write_files>SKILL.md</write_files>
  <action>将 SKILL.md 的"角色红线速查"表替换为双列表格（首要原则 + 禁止），表头改为"角色约束速查"。6 个角色各增加一条正向首要原则。具体内容见 DESIGN.md 注入点 C。</action>
  <verify>grep -c "首要原则（必须保护）" SKILL.md</verify>
  <done>SKILL.md 包含双列"角色约束速查"表，6 个角色各有首要原则和禁止项。AC-3 满足。</done>
  <depends_on></depends_on>
  <e2e_coverage>SKILL.md 角色约束表 → 全阶段角色声明引用</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
</task>

<task id="T02" parallel="false" priority="must" type="config" mode="afk">
  <name>阶段反模式目录：3 个核心阶段各增加反模式清单</name>
  <read_files>SKILL.md</read_files>
  <write_files>SKILL.md, references/stages/3-develop.md, references/stages/4-test.md, references/stages/5-review.md</write_files>
  <action>在 SKILL.md 角色约束速查表之后新增"阶段反模式速查"章节，包含 3-开发(5条)、4-测试(4条)、5-审查(4条)反模式清单。同时在 3 个 reference 文件中追加反模式自检引用。具体内容见 DESIGN.md 注入点 E。</action>
  <verify>grep -c "阶段反模式速查" SKILL.md && grep -c "反模式" references/stages/3-develop.md && grep -c "反模式" references/stages/4-test.md && grep -c "反模式" references/stages/5-review.md</verify>
  <done>SKILL.md 包含"阶段反模式速查"章节，3 个核心阶段各有 ≥4 条反模式。3 个 reference 文件有反模式引用。AC-5 满足。</done>
  <depends_on>T01</depends_on>
  <e2e_coverage>SKILL.md 反模式目录 → 3/4/5 阶段执行时引用</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
</task>

<task id="T03" parallel="false" priority="must" type="config" mode="afk">
  <name>增量闸门：闸门检查增加增量模式描述</name>
  <read_files>SKILL.md</read_files>
  <write_files>SKILL.md</write_files>
  <action>在 SKILL.md 第四步·闸门检查表之后、Handoff 检查之前，新增"增量闸门模式"段落。描述同阶段内二次闸门只验证增量的规则，包括判断条件（读阶段进度字段）和阶段转换时的例外。具体内容见 DESIGN.md 注入点 B。</action>
  <verify>grep -c "增量闸门模式" SKILL.md</verify>
  <done>SKILL.md 闸门检查区域包含"增量闸门模式"段落，描述清晰无歧义。AC-2 满足。</done>
  <depends_on>T02</depends_on>
  <e2e_coverage>SKILL.md 闸门机制 → 全阶段闸门检查引用</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
</task>

<task id="T04" parallel="false" priority="must" type="config" mode="afk">
  <name>反过度优化护栏：LITE 不可跳过场景 + SUGGEST 不可自动执行症状</name>
  <read_files>SKILL.md</read_files>
  <write_files>SKILL.md</write_files>
  <action>两处注入：(1) 第四步闸门检查 LITE 简化闸门列描述扩展——增加 LITE 不可跳过的 3 种场景；(2) 第七步状态更新 SUGGEST 路径安全原则之后——增加不可自动执行的 4 条症状清单。具体内容见 DESIGN.md 注入点 D。</action>
  <verify>grep -c "LITE 不可跳过" SKILL.md && grep -c "SUGGEST 不可自动执行" SKILL.md</verify>
  <done>SKILL.md 包含 LITE 不可跳过场景(≥3条)和 SUGGEST 不可自动执行症状(≥3条)。AC-4 满足。</done>
  <depends_on>T03</depends_on>
  <e2e_coverage>SKILL.md 闸门机制 + 进化系统 → LITE 模式闸门 + SUGGEST 路径引用</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
</task>

<task id="T05" parallel="false" priority="must" type="config" mode="afk">
  <name>主动精炼环：开发阶段 task 完成后自动触发代码精炼</name>
  <read_files>SKILL.md, references/stages/3-develop.md</read_files>
  <write_files>SKILL.md, references/stages/3-develop.md</write_files>
  <action>两处注入：(1) SKILL.md 第六步·加载执行 Token 预算段之后——新增"阶段内精炼环"子章节（4 项检查清单 + LITE 跳过规则）；(2) references/stages/3-develop.md——追加精炼环步骤引用。具体内容见 DESIGN.md 注入点 A。</action>
  <verify>grep -c "阶段内精炼环" SKILL.md && grep -c "精炼环" references/stages/3-develop.md</verify>
  <done>SKILL.md 包含精炼环子章节（4 项检查 + LITE 跳过），3-develop.md 有引用。AC-1 满足。</done>
  <depends_on>T04</depends_on>
  <e2e_coverage>SKILL.md 精炼环 → 3-开发阶段 task 完成后触发 → SUMMARY 产出</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
</task>

<task id="T06" parallel="false" priority="must" type="config" mode="afk">
  <name>验证闭环：开发+审查阶段增加自我验证子步骤</name>
  <read_files>SKILL.md, references/stages/3-develop.md, references/stages/5-review.md</read_files>
  <write_files>SKILL.md, references/stages/3-develop.md, references/stages/5-review.md</write_files>
  <action>三处注入：(1) SKILL.md 第六步·精炼环段之后——新增"阶段内验证闭环"子章节（开发验证 3 步 + 审查验证 3 步 + 记录格式）；(2) references/stages/3-develop.md——追加验证闭环引用；(3) references/stages/5-review.md——追加验证闭环引用。具体内容见 DESIGN.md 注入点 F。</action>
  <verify>grep -c "阶段内验证闭环" SKILL.md && grep -c "验证闭环" references/stages/3-develop.md && grep -c "验证闭环" references/stages/5-review.md</verify>
  <done>SKILL.md 包含验证闭环子章节（开发+审查两场景），3-develop.md 和 5-review.md 有引用。AC-6 满足。</done>
  <depends_on>T05</depends_on>
  <e2e_coverage>SKILL.md 验证闭环 → 3-开发/5-审查 阶段完成前触发 → SUMMARY/REVIEW 记录</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
</task>
