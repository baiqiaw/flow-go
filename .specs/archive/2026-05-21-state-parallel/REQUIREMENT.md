# REQUIREMENT — state-parallel

## 用户故事
作为 flow-go 使用者，我想在多个 Claude Code 会话中同时推进不同的 change，以便提高并行效率，避免串行等待。

## 验收准则（BDD）

### AC-1 每个 change 拥有独立状态
**Given**: flow-go 项目中已有 change A 正在进行（阶段 3-开发）
**When**: 用户在新终端启动新会话，开始 change B
**Then**: change B 有独立的状态信息（阶段、任务、进度），与 change A 的状态完全隔离，互不影响

### AC-2 多会话并行无冲突
**Given**: 终端 1 的会话正在处理 change A，终端 2 的会话正在处理 change B
**When**: 两个会话同时更新各自 change 的状态
**Then**: 各自的状态更新不丢失、不互相覆盖

### AC-3 会话可识别当前 change
**Given**: 项目中有 N 个活跃 change
**When**: 用户在新会话中输入 `go`
**Then**: flow-go 列出所有活跃 change，让用户选择要继续的 change（或开始新 change）

### AC-4 单 change 体验不变
**Given**: 项目中只有 1 个活跃 change（最常见场景）
**When**: 用户在会话中输入 `go`
**Then**: 行为与当前完全一致——自动路由到该 change 的当前阶段，无需额外选择步骤

### AC-5 中断恢复按 change 隔离
**Given**: change A 被中断（中断任务非空），change B 正常运行中
**When**: 用户恢复 change A
**Then**: 仅恢复 change A 的中断任务，change B 的状态不受影响

### AC-6 旧数据自动迁移
**Given**: 项目存在旧格式 STATE.md（单 change 模型），包含活跃 change 信息
**When**: flow-go 首次读取旧格式 STATE.md
**Then**: 自动将旧数据迁移到新格式，不丢失任何状态信息

### AC-7 归档流程正确清理
**Given**: change A 和 change B 都在活跃状态
**When**: change A 完成归档
**Then**: change A 从活跃列表移除，change B 保持活跃不变

## 非功能需求
- 性能：STATE.md 读取和解析不显著增加延迟（< 100ms 额外开销）
- 安全：文件读写不引入竞态条件（通过文件隔离或原子写入保证）
- 兼容：旧格式 STATE.md 必须能自动迁移，不要求手动修改
- 向后兼容：归档的旧 change 数据不受影响

## Out of Scope（范围排除）
- 不做分布式锁或文件锁机制
- 不做多人权限控制或角色分配
- 不做实时状态同步通知
- 不改 PIPELINE.md 的结构
- 不改归档目录结构

## Principles（设计约束原则）
- STATE.md 始终是唯一状态源（不引入额外状态文件如 session registry）
- 最小改动原则：只改必须改的，不趁机重构无关逻辑
- 单 change 场景的用户体验不能退化（零额外操作）
- 所有引用 STATE.md 的脚本和文档必须同步更新

## Key Decisions（关键决策记录）
| 决策 | 理由 | 影响 |
|------|------|------|
| 支持单人多终端和多人协作 | 用户明确要求两者 | 状态模型必须完全隔离，不能假设同一操作者 |
| 真并行执行（非时间片） | 用户明确选择 | 每个会话需要能独立操作自己的 change 状态 |
| 验收含文档更新 | 用户明确要求 | 需要更新 SKILL.md 和所有 references/ 中涉及 STATE.md 的文档 |

## 术语表
| 术语 | 含义 |
|------|------|
| 会话（session） | 一次 Claude Code 对话实例，对应一个终端窗口 |
| 真并行 | 多个 change 各自在独立会话中同时推进，非交替/时间片 |
| 状态隔离 | 不同 change 的状态信息互不影响，各自独立读写 |
