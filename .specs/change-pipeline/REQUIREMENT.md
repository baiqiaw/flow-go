# REQUIREMENT — change-pipeline

## 用户故事
作为 flow-go 使用者，我希望：
1. 需求拆分后后续 change 有明确的排队记录和衔接机制
2. 未完成全流程的 change 可以安全中断并在之后恢复，而非被错误归档
3. 无冲突、无依赖的多个 change / 任务可以并行执行，且不会被多个 AI agent 同时操作同一资源

## 验收准则（BDD）

### AC-1 拆分时自动创建 PIPELINE.md
**Given** 0-需求阶段检测到多子系统，用户确认拆分为 N 个 change
**When** 产品经理完成第一个 change 的 CHANGE.md + REQUIREMENT.md
**Then** 在 `.specs/PIPELINE.md` 中创建排队记录，包含全部 N 个 change（第 1 个标记为 `active`，其余标记为 `pending`），每个 change 包含 change-id、描述、优先级、依赖关系、状态字段

### AC-2 PIPELINE.md 格式
**Given** PIPELINE.md 已创建
**When** 读取文件内容
**Then** 格式为 Markdown 表格，包含以下列：`change-id`、`描述`、`优先级`（MoSCoW）、`依赖`（依赖哪个 change-id）、`状态`（active/pending/completed/skipped/interrupted）、`文件范围`（预期改动的文件 glob）、`备注`

### AC-3 归档后自动衔接
**Given** PIPELINE.md 中存在状态为 `pending` 的 change，且当前 change 归档流程已完成
**When** 归档流程的最后一步
**Then** 系统自动检查 PIPELINE.md，找到下一个 `pending`（按优先级排序，依赖已满足）的 change，将 change-id 写入 STATE.md 的 `Pipeline 待续` 字段，输出提示「📋 Pipeline 下一个：{change-id} — {描述}」，并询问用户是否立即开始

### AC-4 用户确认后自动启动
**Given** 归档衔接提示显示了下一个 pending change
**When** 用户确认"开始"
**Then** 清空 STATE.md 的 `Pipeline 待续` 字段，将该 change 标记为 `active`，创建 `.specs/<id>/` 目录，更新 STATE.md 的 `活跃 Change`，直接进入该 change 的 0-需求阶段（复用拆分时已有的需求信息）

### AC-5 排队管理命令
**Given** `.specs/PIPELINE.md` 文件存在
**When** 用户输入 `排队` / `pipeline` / `backlog`
**Then** 路由到排队管理，显示当前 pipeline 全貌（所有 change 的状态、优先级、依赖），并提供操作选项：开始下一个 / 跳过某个 / 调整优先级 / 手动添加新 change

### AC-6 依赖检查
**Given** PIPELINE.md 中某个 pending change 的 `依赖` 字段引用了另一个 change-id
**When** 该 change 尝试开始（无论是自动衔接还是手动开始）
**Then** 系统检查依赖的 change 是否状态为 `completed`，未完成则提示「⚠️ 依赖未满足：{change-id} 状态为 {status}」并阻止开始

### AC-7 归档时状态更新
**Given** 当前活跃 change 归档完成
**When** 更新 PIPELINE.md
**Then** 该 change 的状态从 `active` 更新为 `completed`，PIPELINE.md 中其他字段不变

### AC-8 无 PIPELINE 时不影响现有流程
**Given** `.specs/PIPELINE.md` 文件不存在
**When** 执行任何 flow-go 操作
**Then** 行为与当前完全一致，不报错，不提示

### AC-8.1 跨会话衔接 — Pipeline 待续恢复
**Given** STATE.md 的 `活跃 Change` 为"无"，但 `Pipeline 待续` 字段非空（值为某个 change-id）
**When** 新会话启动 flow-go（第一步读 STATE.md）
**Then** 系统直接提示「📋 Pipeline 待续：{change-id}，要开始吗？」，用户确认后走 AC-4 流程启动

### AC-8.2 用户暂不执行时保留提示
**Given** 归档衔接提示或跨会话恢复提示显示了下一个 pending change
**When** 用户选择"下次再说"或不响应
**Then** STATE.md 的 `Pipeline 待续` 字段保持不变，下次会话仍会提示。PIPELINE.md 中该 change 保持 `pending` 状态

### AC-9 未完成 change 中断而非归档
**Given** 当前活跃 change 未走完全部 8 阶段（如仅在 0-需求阶段），用户需要暂停去处理其他事
**When** 用户请求暂停/切换 change
**Then** 该 change 在 PIPELINE.md 中标记为 `interrupted`（而非归档到 archive/），记录中断阶段到 STATE.md 的 `中断任务` 字段，.specs/<id>/ 目录和已有工件保持不动

### AC-10 中断恢复 — STATE.md 扫描
**Given** STATE.md 的 `活跃 Change` 为"无"，且 `.specs/` 下存在不在 `archive/` 中的子目录
**When** 用户发起任何 flow-go 操作（如 `go` / `继续`）
**Then** 系统扫描 `.specs/` 目录（排除 `archive/` 和 `evolution/`），列出所有未归档的 change，提示用户选择恢复哪个（如果有 PIPELINE.md 则优先从 pipeline 读取状态）

### AC-11 多 change 并行 — 状态支持
**Given** PIPELINE.md 中存在多个 `pending` change
**When** 用户选择并行启动一个新的 change（当前已有一个 active change）
**Then** 系统允许将新 change 也标记为 `active`（PIPELINE.md 支持多个 active 状态），STATE.md 新增 `并行 Change` 字段记录所有活跃 change-id

### AC-12 并行冲突检测 — 文件范围
**Given** PIPELINE.md 中已有 active change A，其 `文件范围` 字段声明了 `src/auth/**`
**When** 用户尝试并行启动 change B，其 `文件范围` 为 `src/auth/login.py`
**Then** 系统检测到文件范围重叠，输出「⚠️ 冲突：change B 的文件范围与 active change A 重叠（src/auth/login.py）」，建议串行执行或调整范围

### AC-13 并行锁 — 任务级文件锁
**Given** change A 的任务 T01 正在执行，声明改动文件为 `src/api.py`
**When** 另一个 agent 尝试对同一文件执行 change B 的任务
**Then** 系统通过 `.specs/<id>/.lock` 文件检测到锁冲突，提示「🔒 文件锁冲突：src/api.py 被 change A / T01 锁定」，阻止执行

### AC-14 并行锁 — 锁的创建与释放
**Given** 一个任务开始执行
**When** 开发员进入 3-开发阶段执行某个任务
**Then** 系统在该 change 的 .specs/<id>/ 下创建 `.lock` 文件，记录锁定的文件路径、任务 ID 和时间戳。任务完成（SUMMARY.md 产出）后自动删除锁文件

### AC-15 并行安全 — 同任务互斥
**Given** change A 的任务 T01 正在被 agent-1 执行（锁文件存在）
**When** agent-2 也尝试执行同一 change 的同一任务 T01
**Then** 系统检测到任务级锁冲突，提示「🔒 任务 T01 正在由其他 agent 执行」，阻止重复执行

## 非功能需求
- 性能：PIPELINE.md 读写操作 < 100ms（纯文件操作）
- 安全：不引入新的外部依赖
- 兼容：无 PIPELINE.md 时现有流程完全不受影响

## Out of Scope（范围排除）
- 不实现自动拆分逻辑（仍由产品经理人工拆分）
- 不实现 change 间自动依赖检测（人工标注）
- 不实现跨进程的分布式锁（限定为文件锁，适用单机多 agent）

## Principles（设计约束原则）
- 纯文件驱动（Markdown + 文件锁），与 flow-go 现有风格一致
- 渐进增强：PIPELINE.md 不存在时完全不影响现有流程
- 用户确认制：自动衔接仅提示，不自动启动下一个 change
- 并行安全优先：宁可拒绝并行也不允许冲突
- 锁粒度为任务级文件：锁定的是具体文件路径，不是整个 change

## Key Decisions（关键决策记录）
| 决策 | 理由 | 影响 |
|------|------|------|
| PIPELINE.md 独立文件而非 STATE.md 字段 | STATE.md 是单 change 状态，pipeline 是多 change 编排，职责不同 | 新增一个工件文件 |
| 归档衔接为提示而非自动启动 | 用户可能需要休息、调整优先级，强制自动启动体验差 | 归档流程末尾增加 AskUserQuestion |
| 依赖检查为阻塞而非警告 | 未完成的依赖意味着上下文缺失，强行开始会导致返工 | 开始 change 前增加依赖检查步骤 |
| 中断 ≠ 归档 | 归档意味着"已完成全流程"，中断意味着"暂停但可恢复"。语义不同，存储位置不同 | PIPELINE.md 新增 interrupted 状态 |
| 冲突检测基于文件 glob 声明 | 无法自动检测所有文件冲突（需要运行时才知道改哪些文件），改为要求 upfront 声明 | PIPELINE.md 新增 `文件范围` 列 |
| 锁机制用文件锁（.lock 文件） | 单机多 agent 场景下文件锁最简单可靠，不需要分布式协调 | .specs/<id>/.lock 文件 |
| STATE.md 轻量指针 | 跨会话衔接需要在 STATE.md 中留线索（`Pipeline 待续` 字段），PIPELINE.md 是完整数据源，STATE.md 只是指针 | STATE.md 新增 1 个字段 |

## 术语表
| 术语 | 含义 |
|------|------|
| PIPELINE.md | 排队文件，记录所有拆分出的 change 及其状态 |
| 排队 | change 在 pipeline 中的等待状态 |
| 衔接 | 归档/中断后自动提示进入下一个 pending change |
| 依赖 | 一个 change 需要另一个 change 先完成才能开始 |
| 中断 | change 未走完全流程被暂停，不归档，可恢复 |
| 文件范围 | change 预期改动的文件 glob 模式，用于冲突检测 |
| 文件锁 | .specs/<id>/.lock 文件，记录任务正在改动的文件，防止并行冲突 |
