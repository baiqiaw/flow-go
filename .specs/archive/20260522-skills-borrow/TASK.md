# TASK — skills-borrow

## 依赖图
```
T01 [P] ─┬─→ T03 ─→ T04 ──→ T07 → T08 → T09
          └─→ T05 ───────────┘      ↑
T02 [P] ─────────────────────────────┘
T06 [P] ─────────────────────────────┘
```
T01/T02/T06 可并行（无依赖）。T03/T05 依赖 T01。T07 汇聚 T04+T05。T08 汇聚 T02+T04+T05+T06+T07。T09 回归测试。

## 并行分组
- 组 A [并行]：T01(small) + T02(medium) + T06(medium) — 基础设施（模板+脚本修复+调试流程）
- 组 B [并行]：T03(small) + T04(medium) + T05(small) — 阶段文件更新（依赖 T01）
- 组 C：T07(small) — 工件模板更新（等待 T04+T05）
- 组 D：T08(large) — SKILL.md 更新（等待 T02+T04+T05+T06+T07）
- 串行：T09(small) — 回归测试

## 任务列表

<task id="T01" parallel="true" priority="must" type="feature">
  <name>创建 ADR + CONTEXT 模板文件</name>
  <read_files>references/artifacts/spec-artifacts.md</read_files>
  <write_files>references/artifacts/memory-artifacts.md</write_files>
  <action>创建 references/artifacts/memory-artifacts.md，包含两个模板：

1. ADR 模板（编号 NNNN-<slug>.md 格式）：
   - 背景、选项（A/B/C 列表）、决策、理由
   - 存放路径：.specs/adr/NNNN-<slug>.md
   - 三条件前置检查说明（难以逆转 + 无上下文会困惑 + 有真实方案取舍）

2. CONTEXT.md 模板：
   - 结构：Language（术语定义+避免别名）、Relationships（术语关系）、Flagged ambiguities（歧义标记）
   - 存放路径：.specs/CONTEXT.md
   - 规则：只记领域术语、只记定义不记实现、最小化原则

风格与现有 spec-artifacts.md 一致（中文、Markdown 代码块模板、自检清单）。</action>
  <verify>test -f references/artifacts/memory-artifacts.md && grep -c "ADR" references/artifacts/memory-artifacts.md && grep -c "CONTEXT" references/artifacts/memory-artifacts.md</verify>
  <done>memory-artifacts.md 包含 ADR 和 CONTEXT 两个完整模板，格式与 spec-artifacts.md 一致</done>
  <depends_on></depends_on>
  <context_budget>small</context_budget>
  <agent_hint>AFK — 独立创建新文件，无需与其他任务协调</agent_hint>
</task>

<task id="T02" parallel="true" priority="must" type="bugfix">
  <name>修复闸门脚本 + 新增 ADR/CONTEXT 闸门检查</name>
  <read_files>references/scripts/gate_check.py, references/scripts/gate_artifacts.py, references/scripts/validate_state.py</read_files>
  <write_files>references/scripts/gate_check.py, references/scripts/gate_artifacts.py, references/scripts/validate_state.py</write_files>
  <action>修复闸门脚本格式不一致问题 + 新增 ADR/CONTEXT 闸门检查功能：

gate_check.py 修复：
1. --complexity 参数接受大小写（内部 .lower() 转换）
2. 确保所有输出 JSON 格式一致（passed/missing/warnings 字段结构统一）
3. 检查 getattr(args, "stage", 0) 在 quality-gate 模式下的行为是否正确

gate_check.py 新增功能：
4. --stage 0 时（STANDARD/HEAVY）：检查 .specs/CONTEXT.md 是否已创建（仅当 REQUIREMENT.md 术语表有内容时）
5. --stage 1 时（HEAVY）：检查 ADR 三条件评估是否完成（如果设计阶段产出了 ADR，验证 .specs/adr/ 目录下有对应文件）

gate_artifacts.py 修复：
6. 工件清单与 SKILL.md 闸门检查表完全对齐（确保每个闸门行都有对应的检查逻辑）

validate_state.py 修复：
7. 输出格式统一：✅/❌ 标记、缩进、字段名与 gate_check.py 一致
8. 确保错误信息使用一致的中文格式
9. JSON 输出结构与其他脚本对齐

所有脚本修改后必须通过 --help 测试且无报错。</action>
  <verify>cd references/scripts && python3 gate_check.py --help && python3 validate_state.py --help && python3 gate_check.py --stage 1 --change-id skills-borrow --specs-dir ../../.specs/skills-borrow --complexity HEAVY && python3 gate_check.py --stage 1 --change-id skills-borrow --specs-dir ../../.specs/skills-borrow --complexity heavy</verify>
  <done>三个脚本的 --help 和基本功能正常运行，--complexity 接受大小写，输出格式一致，ADR/CONTEXT 闸门检查就位</done>
  <depends_on></depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>AFK — 脚本修复和功能新增，独立于其他任务</agent_hint>
</task>

<task id="T03" parallel="true" priority="must" type="feature">
  <name>需求阶段增加 CONTEXT 自动维护</name>
  <read_files>references/stages/0-requirement.md, references/artifacts/memory-artifacts.md</read_files>
  <write_files>references/stages/0-requirement.md</write_files>
  <action>修改 references/stages/0-requirement.md，增加以下内容：

1. 步骤 4 扩展：术语表写入 `.specs/CONTEXT.md`
   - REQUIREMENT.md 术语表章节完成后，同步写入 .specs/CONTEXT.md
   - 使用 memory-artifacts.md 中的 CONTEXT 模板格式
   - 惰性创建：首次有术语时才创建文件

2. 步骤新增（步骤 4.1）：术语冲突检测
   - 写入前读取 .specs/CONTEXT.md（如存在）
   - 遇到已有术语但定义不同 → 提醒用户确认
   - 遇到已有术语的"避免别名" → 替换为规范术语

3. 影响面判定（步骤 6）扩展：增加 "CONTEXT 需更新" 的自动检查

4. 上下文需求清单新增一行：CONTEXT.md 域语言

保持现有内容不变，仅增量添加。中文注释。</action>
  <verify>grep -c "CONTEXT.md" references/stages/0-requirement.md</verify>
  <done>0-requirement.md 包含 CONTEXT 自动维护步骤和术语冲突检测逻辑</done>
  <depends_on>T01</depends_on>
  <context_budget>small</context_budget>
  <agent_hint>AFK — 单文件增量修改</agent_hint>
</task>

<task id="T04" parallel="true" priority="must" type="feature">
  <name>设计阶段增加 ADR + 深模块 + 原型子阶段</name>
  <read_files>references/stages/1-design.md, references/artifacts/memory-artifacts.md</read_files>
  <write_files>references/stages/1-design.md</write_files>
  <action>修改 references/stages/1-design.md，增加以下内容：

1. 步骤 4（ADR）扩展：
   - ADR 三条件过滤：创建前检查"难以逆转 + 无上下文会困惑 + 有真实方案取舍"三个条件
   - 不满足三条件的决策 → 记录到 DESIGN.md 的"其他决策"章节（非 ADR 文件）
   - ADR 文件写入 `.specs/adr/NNNN-<slug>.md`，使用 memory-artifacts.md 模板
   - 步骤新增（步骤 4.1）：自动扫描 `.specs/adr/` 已有 ADR → 遇到已否决方案时提醒
   - 惰性创建：首次需要 ADR 时才创建 .specs/adr/ 目录

2. 步骤新增（步骤 6.1）：深模块原则指导
   - 接口面积评估（方法数、参数复杂度）
   - "删除测试"：想象删掉模块后复杂度是否重新分散
   - AI 生成代码倾向检查：标记 3-5 行浅函数为"建议合并"

3. 步骤新增（步骤 6.2）：Seams 纪律
   - 一个 Adapter = 假设 Seam（不引入抽象）
   - 两个 Adapter = 真实 Seam（可以引入接口）
   - 检查是否存在"为假设的未来替换加接口"的过度抽象

4. 步骤新增（步骤 7.5，在分段呈现前）：HEAVY 复杂度可选原型子阶段
   - 触发条件：complexity = HEAVY 且设计讨论中有不确定性
   - 两条分支：逻辑原型（终端交互）vs UI 原型（多变体对比）
   - 规则：抛弃型代码、明确标注、回答完问题后必须删除或提炼
   - 原型结论记录到 DESIGN.md 的"原型决策"章节

5. 上下文需求清单新增：CONTEXT.md（域语言 + 已锁决策 + 禁止清单）

6. 自检清单新增：ADR 三条件评估记录、深模块评估、Seams 检查

保持现有内容不变，仅增量添加。</action>
  <verify>grep -c "三条件" references/stages/1-design.md && grep -c "Seams" references/stages/1-design.md && grep -c "原型" references/stages/1-design.md && grep -c "深模块" references/stages/1-design.md</verify>
  <done>1-design.md 包含 ADR 三条件过滤、深模块原则、Seams 纪律、原型子阶段</done>
  <depends_on>T01</depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>HITL — 改动较大，涉及设计阶段核心流程变更，建议人工审阅</agent_hint>
</task>

<task id="T05" parallel="true" priority="must" type="feature">
  <name>任务阶段增加 AFK/HITL + 垂直切片指导</name>
  <read_files>references/stages/2-task.md</read_files>
  <write_files>references/stages/2-task.md</write_files>
  <action>修改 references/stages/2-task.md，增加以下内容：

1. 步骤 1（拆原子任务）扩展：垂直切片原则
   - 每个任务必须是垂直切片（穿透 schema→API→测试，可独立验证）
   - 明确禁止水平切片（按层拆分：所有 schema 一个任务、所有 API 一个任务）
   - 水平切片的信号：任务 action 只涉及单层操作
   - 垂直切片的验证：任务 done 条件包含端到端验证

2. 步骤 2（标并行）扩展：AFK/HITL 标记指导
   - AFK：可完全交给 AI agent 自动执行的任务（无需人工决策、无外部依赖）
   - HITL：需要人工决策/审阅/外部操作的任务
   - COLAB：AI + 人协作完成的任务（默认）
   - 标记原则：优先标记为 AFK；涉及架构决策、设计审阅、外部服务操作 → HITL
   - 并行模式增强：parallel 模式优先将 AFK 任务分配给独立 agent

3. 垂直切片耦合风险应对（对应评审观察）：
   - 允许共享 setup/teardown 任务作为独立前序任务
   - 公共 schema/类型定义可作为独立的前序任务

4. 自检清单新增：垂直切片检查、AFK/HITL 标记检查

保持现有内容不变，仅增量添加。</action>
  <verify>grep -c "垂直切片" references/stages/2-task.md && grep -c "AFK" references/stages/2-task.md && grep -c "HITL" references/stages/2-task.md</verify>
  <done>2-task.md 包含垂直切片原则、AFK/HITL 标记指导和耦合风险应对</done>
  <depends_on>T01</depends_on>
  <context_budget>small</context_budget>
  <agent_hint>AFK — 单文件增量修改</agent_hint>
</task>

<task id="T06" parallel="true" priority="must" type="feature">
  <name>开发阶段增加结构化调试子流程</name>
  <read_files>references/stages/3-develop.md</read_files>
  <write_files>references/stages/3-develop.md</write_files>
  <action>修改 references/stages/3-develop.md，增加以下内容：

1. 步骤新增（步骤 3.1）：结构化调试子流程

   Phase 1 — 建反馈闭环（核心）：
   - 10 种构建方式按优先级排列：失败测试 > curl 脚本 > CLI 调用 > 无头浏览器 > 回放 trace > 抛弃型 harness > 属性/模糊 > bisect harness > 差分循环 > HITL 脚本
   - 迭代优化循环：更快/更尖锐/更确定性
   - 非确定性 bug：提高复现率（50% 可调试，1% 不可调试）
   - 确实无法建循环 → 停下说明，不继续

   Phase 2 — 复现：
   - 确认复现的是用户描述的 bug（不是附近的其他 bug）
   - 确认可跨多次运行复现

   Phase 3 — 可证伪假设：
   - 列出 3-5 个排好序的假设
   - 每个假设必须可证伪："如果 X 是原因，那么改 Y 会让 bug 消失"
   - 展示给用户后再验证

   Phase 4 — 探测：
   - 每个探测映射到具体假设
   - 一次只改一个变量
   - 调试日志用 [DEBUG-xxxx] 前缀标记

   Phase 5 — 修复 + 回归测试：
   - 先写回归测试再修复
   - 如果没有合适的 seam → 记录为架构问题

   Phase 6 — 清理 + 事后分析：
   - 删除 [DEBUG-xxxx] 日志
   - 删除抛弃型原型
   - 提交消息包含正确的假设
   - "什么能防止这个 bug 再次出现？"

2. 快速调试路径：简单 bug（可一步复现）可跳过 Phase 3-4

3. 自检新增：调试日志清理检查、假设记录检查

保持现有内容不变，仅增量添加。</action>
  <verify>grep -c "反馈闭环" references/stages/3-develop.md && grep -c "可证伪" references/stages/3-develop.md && grep -c "DEBUG-" references/stages/3-develop.md</verify>
  <done>3-develop.md 包含完整 6 Phase 结构化调试子流程和快速调试路径</done>
  <depends_on></depends_on>
  <context_budget>medium</context_budget>
  <agent_hint>AFK — 单文件增量修改，内容已充分设计</agent_hint>
</task>

<task id="T07" parallel="false" priority="must" type="feature">
  <name>更新工件模板：task mode 属性 + ADR/CONTEXT 引用</name>
  <read_files>references/artifacts/task-artifacts.md, references/artifacts/spec-artifacts.md, references/artifacts/memory-artifacts.md</read_files>
  <write_files>references/artifacts/task-artifacts.md, references/artifacts/spec-artifacts.md</write_files>
  <action>修改两个工件模板文件：

1. task-artifacts.md：
   - <task> 标签属性定义新增：mode="afk|hitl|colab"（默认 colab）
   - mode 取值说明：afk=AI自动执行、hitl=需人工决策、colab=AI+人协作
   - 标记指导：涉及架构决策/设计审阅/外部操作 → hitl；纯实现/有明确action → afk
   - TASK.md 自检清单新增：mode 字段已填写
   - 示例 task 增加 mode 属性

2. spec-artifacts.md：
   - DESIGN.md 模板 ADR 章节增加三条件过滤说明
   - 新增"ADR 模板引用"指向 memory-artifacts.md
   - 新增"CONTEXT 模板引用"指向 memory-artifacts.md
   - REQUIREMENT.md 自检新增：术语表与 CONTEXT.md 一致性

保持现有内容不变，仅增量添加。</action>
  <verify>grep -c "mode=" references/artifacts/task-artifacts.md && grep -c "memory-artifacts" references/artifacts/spec-artifacts.md</verify>
  <done>task-artifacts.md 包含 mode 属性，spec-artifacts.md 包含 ADR/CONTEXT 模板引用</done>
  <depends_on>T04, T05</depends_on>
  <context_budget>small</context_budget>
  <agent_hint>AFK — 两个工件模板的增量更新</agent_hint>
</task>

<task id="T08" parallel="false" priority="must" type="feature">
  <name>更新 SKILL.md 主调度：CONTEXT/ADR 路由 + 闸门更新</name>
  <read_files>SKILL.md</read_files>
  <write_files>SKILL.md</write_files>
  <action>修改 SKILL.md，增加以下内容：

1. 第一步（读状态）第 7 点扩展：
   - 读取 .specs/CONTEXT.md（如存在）→ 注入到会话上下文
   - 读取 .specs/adr/（如存在）→ 统计 ADR 数量，提示"已有 N 条架构决策记录"

2. 第三步（意图路由）扩展：
   - 新增路由："原型" / "prototype" → 进入设计阶段的原型子流程（仅 HEAVY）

3. 第四步（闸门检查）扩展：
   - 阶段 1 闸门新增（HEAVY）：检查 ADR 三条件评估是否完成
   - 阶段 0 闸门新增（STANDARD/HEAVY）：检查 CONTEXT.md 是否已创建（如涉及新术语）

4. 第五步（角色声明）扩展：
   - 角色声明增加 CONTEXT 术语提示（如"当前项目有 N 个领域术语"）

5. 第七步（状态更新）扩展：
   - 设计阶段完成时：检查是否产出了新 ADR，如有则提示"新增 N 条 ADR"
   - 归档时：CONTEXT.md 和 .specs/adr/ 不删除（跨 change 持久）

6. 闸门脚本化验证说明更新：
   - gate_check.py 新增 --check-adr 和 --check-context 选项说明

7. 并行模式调度增强（影响 AC-4）：
   - 在第三步"并行"/"parallel"路由中，读取 TASK.md 各 task 的 mode 属性
   - AFK 任务优先分配给独立 agent 执行
   - HITL 任务留在当前会话等待人工决策
   - COLAB 任务由当前会话驱动（默认行为）

保持现有内容不变，仅增量修改。注意 SKILL.md 是 skill 定义文件，格式严格，修改时保持一致性。</action>
  <verify>grep -c '\.specs/CONTEXT\.md' SKILL.md && grep -c '\.specs/adr/' SKILL.md && grep -c 'AFK' SKILL.md && grep -c '原型' SKILL.md</verify>
  <done>SKILL.md 包含 CONTEXT/ADR 路由、闸门更新、原型路由</done>
  <depends_on>T02, T04, T05, T06, T07</depends_on>
  <context_budget>large</context_budget>
  <agent_hint>HITL — SKILL.md 是核心文件，改动影响全局，建议人工审阅每处修改</agent_hint>
</task>

<task id="T09" parallel="false" priority="must" type="chore">
  <name>回归测试：验证所有改动的一致性</name>
  <read_files>references/scripts/gate_check.py, references/scripts/validate_state.py, references/stages/0-requirement.md, references/stages/1-design.md, references/stages/2-task.md, references/stages/3-develop.md, references/artifacts/memory-artifacts.md, references/artifacts/task-artifacts.md, references/artifacts/spec-artifacts.md</read_files>
  <write_files>无</write_files>
  <action>执行回归测试验证所有改动：

1. 闸门脚本格式一致性：
   - python3 references/scripts/gate_check.py --stage 1 --change-id skills-borrow --specs-dir .specs/skills-borrow --complexity HEAVY
   - python3 references/scripts/gate_check.py --stage 1 --change-id skills-borrow --specs-dir .specs/skills-borrow --complexity heavy
   - 两者输出应完全一致
   - python3 references/scripts/validate_state.py --state-file STATE.md --specs-dir .specs/

2. 新增文件检查：
   - test -f references/artifacts/memory-artifacts.md
   - grep "ADR" references/artifacts/memory-artifacts.md
   - grep "CONTEXT" references/artifacts/memory-artifacts.md

3. 阶段文件一致性：
   - 每个阶段文件都引用了 CONTEXT.md
   - 0-requirement.md 包含 CONTEXT 维护步骤
   - 1-design.md 包含 ADR 三条件、深模块、Seams、原型
   - 2-task.md 包含垂直切片、AFK/HITL
   - 3-develop.md 包含 6 Phase 调试流程

4. 工件模板一致性：
   - task-artifacts.md 包含 mode 属性
   - spec-artifacts.md 引用 memory-artifacts.md

5. SKILL.md 一致性：
   - 包含 CONTEXT/ADR 路由
   - 闸门检查包含新检查项

6. 交叉一致性：所有文件中使用相同的术语（CONTEXT.md、.specs/adr/、AFK/HITL/COLAB、垂直切片、深模块、Seams 纪律）

输出测试结果报告。</action>
  <verify>echo "回归测试脚本执行中..." && python3 references/scripts/gate_check.py --stage 0 --change-id skills-borrow --specs-dir .specs/skills-borrow --complexity heavy && python3 references/scripts/gate_check.py --stage 0 --change-id skills-borrow --specs-dir .specs/skills-borrow --complexity HEAVY && echo "全部通过"</verify>
  <done>所有闸门脚本运行正常，格式一致，新增文件/章节齐全，术语统一</done>
  <depends_on>T08</depends_on>
  <context_budget>small</context_budget>
  <agent_hint>HITL — 需要人工确认测试结果和格式一致性</agent_hint>
</task>
