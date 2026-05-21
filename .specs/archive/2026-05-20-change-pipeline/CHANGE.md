# CHANGE — change-pipeline

## Why（为什么做）
flow-go 存在三个流程编排缺陷：

**缺陷 1：拆分后后续 change 丢失**
0-需求阶段检测到多子系统时建议拆分，但拆分后仅创建第一个 change，后续 change 无记录、无优先级、无依赖、无衔接。归档第一个后剩余的"消失"了。

**缺陷 2：未完成 change 被错误归档**
当需要暂停当前 change 去处理更紧急的事（如刚才暂停 evolution-pipeline-p0 去处理本 change），未走完全流程的 change 被直接归档到 archive/，丢失了中断点信息。正确做法是标记为中断而非归档。此外，当 STATE.md 丢失活跃 change 信息时（如新会话），缺少从 .specs/ 目录扫描恢复的机制。

**缺陷 3：强制串行导致效率低**
当前所有 change / 任务强制串行，但无冲突、无依赖的多个 change / 多个任务完全可以并行执行（特别是在多 AI agent 场景下）。缺少冲突检测、锁机制和并行安全策略。

## What（做什么）
新增 `.specs/PIPELINE.md` 文件驱动的 change 排队 + 中断恢复 + 并行安全机制：
1. **PIPELINE.md 工件**：记录排队 change 列表，包含 change-id、描述、优先级、依赖关系、状态（active/pending/completed/skipped/interrupted）
2. **0-需求拆分联动**：拆分确认时自动创建 PIPELINE.md 并写入排队列表
3. **归档/中断衔接**：归档完成后检查 PIPELINE.md 提示下一个；中断时标记为 interrupted 而非归档
4. **中断恢复**：STATE.md 无活跃 change 时扫描 .specs/ 目录恢复
5. **排队管理命令**：新增 `排队` / `pipeline` / `backlog` 路由关键词
6. **并行执行**：支持多个 active change 并行，含冲突检测和锁机制

## 影响面
- 涉及模块：SKILL.md（路由表+状态更新+并行支持）、references/stages/0-requirement.md（拆分步骤+文件范围声明）、references/stages/3-develop.md（锁机制）、references/stages/special-flows.md（归档/中断流程）、references/artifacts/meta-artifacts.md（PIPELINE 工件模板+锁文件模板）
- 数据库变更：否
- API 变更：否
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- 不实现自动拆分逻辑（仍由产品经理在 0-需求阶段人工拆分）
- 不实现 change 之间的自动依赖检测
- 不实现跨进程的分布式锁（锁机制限定为文件锁，适用于单机多 agent 场景）

## 验收线
PIPELINE.md 机制完整实现，从拆分创建到归档/中断衔接形成闭环，排队管理命令可用，中断恢复和并行执行能力就绪。

## 路径建议
增量，理由：新增一个工件文件 + 修改 4 个流程文件的局部段落，不改变现有阶段流程的核心逻辑。
