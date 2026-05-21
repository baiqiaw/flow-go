# CHANGE — state-parallel

## Why（为什么做）
当前 STATE.md 采用单 change 单会话模型：所有状态（活跃 Change、阶段、任务、中断）写在一个文件的单一字段中。无法支持：
1. 同一用户开多个 Claude Code 终端同时处理不同 change（写冲突）
2. 多人各自启动会话处理各自负责的 change（状态互相覆盖）
3. 真并行执行——每个 change 需要独立状态，互不干扰

## What（做什么）
重构 STATE.md 的数据结构，从"单一活跃 change"模型改为"多 change 并行"模型。每个 change 拥有独立的状态信息（阶段、任务、进度、所属会话），多个会话可以同时读写各自负责的 change 状态而不互相干扰。同步更新 flow-go skill 中所有引用 STATE.md 的相关逻辑和文档。

## 影响面
- 涉及模块：STATE.md、SKILL.md、references/stages/（所有阶段文件）、references/special-flows.md、references/sync-workflow.md、references/artifacts/meta-artifacts.md、validate_state.py、gate_check.py 等脚本
- 数据库变更：否
- API 变更：否
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- 不做分布式锁或文件锁机制（依赖文件隔离本身来避免冲突）
- 不做多人权限控制或角色分配
- 不做实时状态同步通知（如 WebSocket 推送）
- 不改 PIPELINE.md 的结构（仅适配新的 STATE.md 格式）
- 不改归档目录结构

## 验收线
STATE.md 新格式能正确跟踪多个并行 change，每个 change 有独立状态；多个 Claude Code 会话可同时操作不同 change 互不干扰；旧 STATE.md 可自动迁移；flow-go 全部文档和脚本同步更新。

## 路径建议
完整，理由：涉及 flow-go 核心状态管理重构，影响所有阶段文件的读写逻辑，需要全面更新以确保一致性。
