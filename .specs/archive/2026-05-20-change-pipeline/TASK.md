# TASK — change-pipeline

## 依赖图
```
T01 (meta-artifacts 基础)
├── T02 [P] (SKILL.md 路由+状态)
├── T03 [P] (0-requirement 拆分联动)
├── T04 [P] (3-develop 锁机制)
└── T05 [P] (special-flows 归档/中断/回溯)
```
T01 为基础任务，定义 PIPELINE.md、.lock、STATE.md 的新增模板和 schema。T02-T05 均依赖 T01 中的格式定义，但相互独立可并行执行。

## 并行分组
- 组 A：T01 (medium) — 基础工件定义，独占执行
- 组 B [并行]：T02(small) + T03(small) + T04(small) + T05(medium) — 4 个文件独立修改，互不依赖

## 任务列表

<task id="T01" parallel="false" priority="must" type="feature">
  <name>meta-artifacts.md 基础工件定义更新</name>
  <read_files>references/artifacts/meta-artifacts.md</read_files>
  <write_files>references/artifacts/meta-artifacts.md</write_files>
  <action>在 meta-artifacts.md 中完成以下 6 项更新：
1. STATE.md Schema：新增 `Pipeline 待续`（格式 `<change-id>` 或 `无`，在 `中断任务` 之后）和 `并行 Change`（格式 `<id1>,<id2>` 或 `无`，在 `Pipeline 待续` 之后）字段定义
2. STATE.md 格式约束：字段数 5 → 7，新增 Pipeline 待续 和 并行 Change 的校验规则（Pipeline 待续 非空时值须为 .specs/ 下存在的 change-id 或 PIPELINE.md 中 pending 的 change-id；并行 Change 非空时各 id 须在 PIPELINE.md 中为 active）
3. STATE.md 完整性校验：新增 Pipeline 待续 和 并行 Change 存在性检查项
4. STATE.md 模板：更新为包含 7 个字段的 Markdown 标题+列表格式
5. 新增 PIPELINE.md 模板章节：完整的 Markdown 表格模板（7 列：change-id/描述/优先级/依赖/状态/文件范围/备注），5 种状态枚举（active/pending/completed/skipped/interrupted），格式约束 6 条
6. 新增 .lock 文件模板章节：JSON 格式模板（task_id/files/agent_id/timestamp），约束 5 条</action>
  <verify>cd /home/cgh/.claude/skills/flow-go && grep -c 'Pipeline 待续' references/artifacts/meta-artifacts.md && grep -c '\.lock' references/artifacts/meta-artifacts.md && grep -c 'PIPELINE —' references/artifacts/meta-artifacts.md</verify>
  <done>meta-artifacts.md 包含更新后的 STATE.md schema（7 字段）+ PIPELINE.md 完整模板 + .lock 完整模板，所有格式约束和校验规则已补充</done>
  <depends_on></depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>基础任务，需完整读取现有 meta-artifacts.md 后增量修改</agent_hint>
</task>

<task id="T02" parallel="true" priority="must" type="feature">
  <name>SKILL.md 路由表+状态读写更新</name>
  <read_files>SKILL.md</read_files>
  <write_files>SKILL.md</write_files>
  <action>在 SKILL.md 中完成以下 4 处修改：
1. 路由表（第三步 意图路由表格）：在 `废弃` 行和 `飞轮巡检` 行之间新增一行：`排队` / `pipeline` / `backlog` → 排队管理流程（加载 stages/special-flows.md 中排队管理段落）
2. 步骤1 读状态：在现有第 5 点之后追加第 6 点 — `Pipeline 待续` 非空且 `活跃 Change` 为空 → 优先输出「📋 Pipeline 待续：{change-id}，要开始吗？」；用户确认"开始"后执行 AC-4 启动流程：清空 `Pipeline 待续` 字段 → PIPELINE.md 中该 change 标记为 `active` → 创建 `.specs/<id>/` 目录 → 更新 STATE.md `活跃 Change` → 路由到 0-需求（复用拆分时已有的需求信息）；`并行 Change` 非空 → 输出当前并行状态概览
3. 步骤7 状态更新：在归档相关说明后新增 — 归档完成后 Pipeline 衔接检查（注意：归档流程内部的衔接逻辑由 T05 修改 special-flows.md 归档步骤 8.5 实现，此处仅添加步骤 7 的触发声明：归档流程完成后如果 `Pipeline 待续` 已被写入，在步骤 7 状态更新时输出衔接提示）。中断流程声明：用户请求暂停时路由到中断流程（由 T05 修改 special-flows.md 实现）
4. 步骤7 状态更新：新增中断流程的 STATE.md 更新规则 — 用户请求暂停时，PIPELINE.md 中状态改为 interrupted，STATE.md 更新中断任务字段</action>
  <verify>cd /home/cgh/.claude/skills/flow-go && grep -c '排队.*pipeline.*backlog' SKILL.md && grep -c 'Pipeline 待续' SKILL.md && grep -c 'interrupted' SKILL.md</verify>
  <done>SKILL.md 路由表含排队管理入口，步骤1含 Pipeline 待续 检查 + AC-4 启动流程，步骤7含归档衔接声明和中断流程 STATE.md 更新规则</done>
  <depends_on>T01</depends_on>
  <context_budget>small</context_budget>
  <agent_hint>可与其他任务并行执行，仅修改 SKILL.md</agent_hint>
</task>

<task id="T03" parallel="true" priority="must" type="feature">
  <name>0-requirement.md 拆分联动增强</name>
  <read_files>references/stages/0-requirement.md</read_files>
  <write_files>references/stages/0-requirement.md</write_files>
  <action>在 0-requirement.md 步骤2（多子系统检测）中扩展拆分确认后的行为：
1. 用户确认拆分后：在「当前 change 保留最核心子系统，其余排队等待」之后，新增子步骤：(a) 创建 `.specs/PIPELINE.md`，写入 N 个 change 行（第 1 个 active，其余 pending），每行包含 7 列（change-id/描述/优先级/依赖/状态/文件范围/备注）
2. 新增文件范围声明：拆分时要求用户为每个 change 声明预期改动的文件 glob 模式，填入 PIPELINE.md 的 `文件范围` 列
3. 新增依赖声明：拆分时询问 change 间依赖关系，填入 PIPELINE.md 的 `依赖` 列
4. 更新输出清单：新增 `.specs/PIPELINE.md`（如触发拆分）</action>
  <verify>cd /home/cgh/.claude/skills/flow-go && grep -c 'PIPELINE.md' references/stages/0-requirement.md && grep -c '文件范围' references/stages/0-requirement.md && grep -c '依赖声明' references/stages/0-requirement.md</verify>
  <done>0-requirement.md 步骤2含 PIPELINE.md 创建、文件范围声明、依赖声明子步骤，输出清单含 PIPELINE.md</done>
  <depends_on>T01</depends_on>
  <context_budget>small</context_budget>
  <agent_hint>可与其他任务并行执行，仅修改 0-requirement.md</agent_hint>
</task>

<task id="T04" parallel="true" priority="must" type="feature">
  <name>3-develop.md 锁机制</name>
  <read_files>references/stages/3-develop.md</read_files>
  <write_files>references/stages/3-develop.md</write_files>
  <action>在 3-develop.md 中新增锁机制步骤：
1. 步骤5（扫 LESSONS.md）后、步骤6（TDD）前新增锁检查步骤：读取 `.specs/<id>/.lock`（如存在），检查 task_id 是否为当前任务 — 如非当前任务则阻止并输出「🔒 任务 {id} 正在由 {agent_id} 执行」；如不存在则继续
2. 锁检查通过后、步骤6（TDD）前新增锁创建步骤：写入 `.specs/<id>/.lock`（JSON：task_id + files 列表 + agent_id + timestamp）
3. 步骤9（写 SUMMARY）后、步骤10（交叉评审）前新增锁释放步骤：确认 SUMMARY.md 已写入后删除 `.specs/<id>/.lock`
4. 在自检清单中新增：锁文件已清理（SUMMARY 写完后 .lock 不存在）</action>
  <verify>cd /home/cgh/.claude/skills/flow-go && grep -c '\.lock' references/stages/3-develop.md && grep -c '锁检查' references/stages/3-develop.md && grep -c '锁创建' references/stages/3-develop.md && grep -c '锁释放' references/stages/3-develop.md</verify>
  <done>3-develop.md 含完整的锁检查→锁创建→锁释放流程，自检清单含锁清理项</done>
  <depends_on>T01</depends_on>
  <context_budget>small</context_budget>
  <agent_hint>可与其他任务并行执行，仅修改 3-develop.md</agent_hint>
</task>

<task id="T05" parallel="true" priority="must" type="feature">
  <name>special-flows.md 归档衔接+中断流程+回溯增强</name>
  <read_files>references/stages/special-flows.md</read_files>
  <write_files>references/stages/special-flows.md</write_files>
  <action>在 special-flows.md 中完成以下 4 组修改：

A. 归档流程修改（在步骤9 STATE.md 清理之前）：
1. 步骤8后新增步骤8.5 — Pipeline 衔接检查：读取 .specs/PIPELINE.md（如存在），找下一个 pending change（按优先级排序，依赖已完成），找到 → STATE.md 写入 `Pipeline 待续` 字段 → 输出「📋 Pipeline 下一个：{change-id} — {描述}」→ 询问用户是否立即开始。用户确认 → 走 AC-4 启动流程。用户拒绝 → 保留字段
2. 步骤9 STATE.md 清空时保留 `Pipeline 待续` 字段值（如有）
3. 在归档自检清单新增：Pipeline 衔接已检查

B. 新增「中断」流程（在归档和废弃之间）：
1. 触发条件：用户请求暂停/切换 change，或当前 change 未走完全流程需要搁置
2. 步骤：(a) 确认中断目标（取 STATE.md 活跃 Change）(b) PIPELINE.md 中状态改为 interrupted (c) STATE.md 更新中断任务字段记录中断阶段 (d) .specs/<id>/ 目录和已有工件保持不动 (e) STATE.md 活跃 Change 清空（允许切换到其他 change）
3. 闸门：用户显式确认中断（区分于归档）
4. 自检清单

C. 新增「并行启动」流程（在中断和废弃之间，对应 AC-11/AC-12）：
1. 触发条件：用户请求并行启动新 change（当前已有 active change）
2. 步骤：(a) 读取 PIPELINE.md 中所有 active change 的 `文件范围` 列 (b) 与新 change 的文件范围做 glob 重叠检测 (c) 无冲突 → PIPELINE.md 标记新 change 为 active → STATE.md `并行 Change` 字段追加新 change-id → 路由到 0-需求 (d) 有冲突 → 输出「⚠️ 冲突：{新change} 的文件范围与 active {已有change} 重叠（{重叠路径}）」→ 建议串行执行或调整范围
3. 闸门：用户确认并行启动 + 文件范围无冲突
4. 自检清单

D. 回溯流程增强：
1. 新增步骤（在现有步骤1后）：检查 STATE.md `Pipeline 待续` 字段，非空则优先提示
2. 新增步骤（在现有步骤9归档扫描后）：扫描 .specs/ 下所有非 archive/evolution 的子目录，列出未归档 change，检查是否有 PIPELINE.md 关联状态
3. 新增步骤：残留锁检测 — 扫描 .specs/ 下所有 .lock 文件，检查对应任务是否已有 SUMMARY.md（有 SUMMARY 的锁视为残留，提示清理）</action>
  <verify>cd /home/cgh/.claude/skills/flow-go && grep -c 'Pipeline 衔接' references/stages/special-flows.md && grep -c '## 中断' references/stages/special-flows.md && grep -c '残留锁' references/stages/special-flows.md && grep -c '并行启动' references/stages/special-flows.md</verify>
  <done>special-flows.md 含归档 Pipeline 衔接步骤、独立的中断流程、并行启动流程（AC-11/AC-12）、回溯流程的 Pipeline/残留锁增强</done>
  <depends_on>T01</depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>修改量最大的任务，需完整读取 special-flows.md 后增量修改三个区域</agent_hint>
</task>
