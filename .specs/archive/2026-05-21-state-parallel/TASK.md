# TASK — state-parallel

## 依赖图

```
T01 (格式定义+迁移)
 ├── T02 (SKILL.md 多change路由) [P] ─┐
 ├── T03 (stages/0-7 写入目标) [P]     ├── T07 (最终验证+迁移测试)
 ├── T04 (special-flows.md) [P]        │
 ├── T05 (validate+gate_check) [P]     │
 └── T06 (其余脚本+文档) [P]           ─┘
```

## 并行分组
- **串行链**：T01 → T02~T06（并行）
- **并行组 A**（T01 完成后）：T02 / T03 / T04 / T05 / T06 同时可做
- **串行收尾**：T07（最终验证）

---

### T01
- id: T01
- name: 定义新格式 + 更新 meta-artifacts.md + 实现 SKILL.md 迁移逻辑
- type: refactor
- priority: Must Have
- read_files:
  - references/artifacts/meta-artifacts.md
  - SKILL.md（第一步·读状态 + 第七步·状态更新）
- write_files:
  - references/artifacts/meta-artifacts.md
  - SKILL.md
- action:
  1. 在 meta-artifacts.md 中定义新的 STATE.md Schema（项目级索引表格式）和 .specs/<id>/STATE.md Schema（change 级详情格式），替换旧的 7 字段模板
  2. 在 SKILL.md 第一步·读状态中添加旧格式检测逻辑：当 STATE.md 的「活跃 Change」值为非表格单行文本且非"无"时，判定为旧格式
  3. 添加自动迁移逻辑：读取旧格式的所有字段 → 写入新格式 STATE.md（索引表）+ 创建 .specs/<id>/STATE.md（详情字段）→ 保留旧内容为注释备份
  4. 更新 SKILL.md 第七步·状态更新的写入路径说明：阶段内高频写 .specs/<id>/STATE.md，阶段转换同步更新 STATE.md 索引表
- verify:
  - `grep -c "活跃 Change" references/artifacts/meta-artifacts.md` 确认模板包含表格格式
  - `grep -c "is_old_format\|旧格式检测\|自动迁移" SKILL.md` 确认迁移逻辑存在
  - `grep -c "\.specs/<id>/STATE.md\|per-change STATE" SKILL.md` 确认写入路径已更新
- done: meta-artifacts.md 含新 Schema 模板；SKILL.md 含旧格式检测 + 自动迁移 + 新写入路径
- depends_on: (无)
- context_budget: medium
- agent_hint: 基础任务，需优先完成，后续所有任务依赖此

### T02
- id: T02
- name: 更新 SKILL.md 多 change 路由逻辑
- type: refactor
- priority: Must Have
- read_files:
  - SKILL.md（第一步·读状态）
- write_files:
  - SKILL.md
- action:
  1. 在第一步·读状态中添加多 change 检测：解析 STATE.md 索引表获取活跃 change 列表
  2. 实现 0/1/N 分支逻辑：
     - 活跃数 = 0：直接进入 0-需求（不变）
     - 活跃数 = 1：自动读 .specs/<id>/STATE.md → 路由（AC-4 零操作）
     - 活跃数 > 1：列出所有活跃 change → AskUserQuestion 让用户选 → 读选中 change 的 STATE.md → 路由
  3. 更新第三步·意图路由中的 `go`/`下一步`/`next` 分支：STATE 有活跃变更 → 从 per-change STATE 读取当前阶段
  4. 更新第七步·状态更新：启动新 change 时创建 .specs/<id>/STATE.md 并在 STATE.md 索引表添加行
- verify:
  - `grep -c "活跃数.*=.*0\|活跃数.*=.*1\|活跃数.*>.*1" SKILL.md` 确认分支逻辑存在
  - `grep -c "AskUserQuestion\|用户选" SKILL.md` 确认多 change 选择机制存在
  - `grep -c "\.specs/<id>/STATE.md" SKILL.md` 确认 per-change 读取路径
- done: SKILL.md 支持 0/1/N change 自动路由 + 新 change 启动创建 per-change STATE
- depends_on: T01
- context_budget: small

### T03 [P]
- id: T03
- name: 更新 stages/0-7 阶段进度写入目标
- type: refactor
- priority: Must Have
- read_files:
  - references/stages/0-requirement.md
  - references/stages/1-design.md
  - references/stages/2-task.md
  - references/stages/3-develop.md
  - references/stages/4-test.md
  - references/stages/5-review.md
  - references/stages/6-deploy.md
  - references/stages/7-acceptance.md
- write_files:
  - references/stages/0-requirement.md
  - references/stages/1-design.md
  - references/stages/2-task.md
  - references/stages/3-develop.md
  - references/stages/4-test.md
  - references/stages/5-review.md
  - references/stages/6-deploy.md
  - references/stages/7-acceptance.md
- action:
  在所有 8 个 stage 文件中，将中断恢复章节中的「更新 STATE.md 的 `阶段进度` 字段」改为「更新 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段」。同时将「会话恢复时读 `阶段进度`」改为「会话恢复时读 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段」。修改模式一致，8 个文件做相同类型的改动。
- verify:
  - `grep -rl "更新 STATE.md 的" references/stages/` 应返回空（旧的写入路径已替换）
  - `grep -rl "\.specs/<change-id>/STATE.md" references/stages/` 应返回 8 个文件
  - `grep -c "阶段进度" references/stages/0-requirement.md` 确认字段仍被引用
- done: 8 个 stage 文件的阶段进度读写目标全部改为 per-change STATE.md
- depends_on: T01
- context_budget: large
- agent_hint: 模板化改动（8文件相同模式），虽 large 但可流式完成，不拆分

### T04 [P]
- id: T04
- name: 更新 special-flows.md 所有流程
- type: refactor
- priority: Must Have
- read_files:
  - references/stages/special-flows.md
- write_files:
  - references/stages/special-flows.md
- action:
  1. 归档流程（含 Pipeline 衔接子步骤 8.5）：归档完成后从 STATE.md 索引表移除该 change 行 + 删除 .specs/<id>/STATE.md；Pipeline 衔接子步骤更新为启动时在索引表添加行 + 创建 per-change STATE
  2. 中断流程：中断任务字段写入 .specs/<id>/STATE.md（而非项目 STATE.md）
  3. 并行启动流程：在 STATE.md 索引表新增行 + 创建 .specs/<id>/STATE.md
  4. 废弃流程：从索引表移除 + 清理 per-change STATE
  5. 回溯流程：从 .specs/<id>/STATE.md 读取所有字段进行状态分析
  6. 热修流程：将输入中的 STATE.md 引用更新为 `.specs/<id>/STATE.md`（从会话上下文获取 change-id）
  7. 归档维护流程：确认无需更新（输入为 .specs/archive/ARCHIVE-INDEX.md，不涉及 STATE.md 读写）
- verify:
  - `grep -c "索引表" references/stages/special-flows.md` 确认索引操作存在
  - `grep -c "\.specs/<id>/STATE.md\|per-change STATE" references/stages/special-flows.md` 确认 per-change 引用
  - `grep -c "移除该 change 行\|删除.*STATE.md" references/stages/special-flows.md` 确认归档清理
- done: 6 个特殊流程（归档含Pipeline衔接、中断、并行启动、废弃、回溯、热修）全部适配新双文件结构；归档维护确认无需更新
- depends_on: T01
- context_budget: medium

### T05 [P]
- id: T05
- name: 更新 validate_state.py + gate_check.py
- type: refactor
- priority: Must Have
- read_files:
  - references/scripts/validate_state.py
  - references/scripts/gate_check.py
- write_files:
  - references/scripts/validate_state.py
  - references/scripts/gate_check.py
- action:
  1. validate_state.py：
     - 更新 REQUIRED_FIELDS：项目 STATE.md 只校验「活跃 Change 表」+「Pipeline 待续」+「更新时间」
     - 新增 .specs/<id>/STATE.md 校验：检查当前阶段/当前任务/中断任务/阶段进度/更新时间
     - 新增一致性校验：STATE.md 索引表中每个 change 的「阶段」值与 .specs/<id>/STATE.md 的「当前阶段」匹配
     - 新增 --change-id 参数：校验指定 change 的 per-change STATE
  2. gate_check.py：
     - 新增 --change-id 参数
     - 闸门校验从 .specs/<change-id>/STATE.md 读取当前阶段，不再从项目 STATE.md 读取
- verify:
  - `python3 references/scripts/validate_state.py --help 2>&1 | grep -c "change-id"` 确认新参数
  - `grep -c "索引表\|per.change\|\.specs.*STATE" references/scripts/validate_state.py` 确认新格式校验
  - `grep -c "change.id" references/scripts/gate_check.py` 确认参数传递
- done: 两个脚本支持新格式 + 一致性校验 + --change-id 参数
- depends_on: T01
- context_budget: medium

### T06 [P]
- id: T06
- name: 更新其余脚本 + 文档文件
- type: refactor
- priority: Should Have
- read_files:
  - references/scripts/trace_collector.py
  - references/scripts/evolution_signal.py
  - references/sync-workflow.md
  - .codex/instructions.md
  - README.md
- write_files:
  - references/scripts/trace_collector.py
  - references/scripts/evolution_signal.py
  - references/sync-workflow.md
  - .codex/instructions.md
  - README.md
- action:
  1. trace_collector.py：从 .specs/<change-id>/STATE.md 读取活跃 Change/当前阶段/当前任务/阶段进度
  2. evolution_signal.py：从 per-change STATE 检测热修标记
  3. sync-workflow.md：更新同步时读取状态的路径描述
  4. .codex/instructions.md：更新 STATE.md 字段描述为新的双文件结构
  5. README.md：更新状态架构描述为索引+per-change 详情
- verify:
  - `grep -c "\.specs.*STATE.md\|per.change" references/scripts/trace_collector.py` 确认路径更新
  - `grep -c "\.specs.*STATE.md\|per.change" references/scripts/evolution_signal.py` 确认路径更新
  - `grep -c "索引\|per-change\|\.specs.*STATE" references/sync-workflow.md .codex/instructions.md README.md` 确认文档更新
- done: 2 个脚本 + 3 个文档文件全部适配新格式
- depends_on: T01
- context_budget: medium
- agent_hint: 可与其他并行任务同时执行

### T07
- id: T07
- name: 最终验证 + 迁移测试
- type: chore
- priority: Must Have
- read_files:
  - SKILL.md
  - references/artifacts/meta-artifacts.md
  - references/scripts/validate_state.py
  - STATE.md（当前项目 STATE）
- write_files:
  - (无，只读验证)
- action:
  1. 构造旧格式 STATE.md 测试用例（单 change 模型），验证迁移检测和自动迁移逻辑描述完整
  2. 运行 validate_state.py 验证当前项目 STATE.md 格式（注意：当前仍是旧格式，迁移后应为新格式）
  3. 全文搜索 SKILL.md 和 references/ 确认不存在遗漏的旧格式 STATE.md 引用（如「当前阶段」写入项目 STATE.md）
  4. 检查所有 AC 对应的任务覆盖：AC-1(T01) / AC-2(T01+T02) / AC-3(T02) / AC-4(T02) / AC-5(T04) / AC-6(T01) / AC-7(T04)
- verify:
  - `grep -rn "更新 STATE.md 的 \`当前阶段\`" references/stages/ references/stages/special-flows.md` 应返回空
  - `grep -rn "\.specs/<.*>/STATE.md" SKILL.md references/ | wc -l` 确认 per-change STATE 引用覆盖所有必要位置
  - 逐条检查 7 条 AC 是否有对应任务覆盖
- done: 旧格式引用全部替换；7 条 AC 全部有任务覆盖；无遗漏
- depends_on: T02, T03, T04, T05, T06
- context_budget: small
- agent_hint: 只读验证，不修改文件，依赖所有实现任务完成
