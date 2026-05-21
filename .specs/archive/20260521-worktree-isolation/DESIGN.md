# DESIGN — worktree-isolation

## 架构图

```
                          flow-go 工作目录上下文
 ┌─────────────────────────────────────────────────────────────────┐
 │                        主仓库（main）                            │
 │  STATE.md ───── 索引表（追踪所有活跃 change）                     │
 │  .specs/<id>/ ── 每个change的spec工件                            │
 │  .claude/worktrees/<id>/ ── worktree 目录                       │
 └─────────────────────────────────────────────────────────────────┘

 阶段 0-需求        阶段 1-设计        阶段 2~5              归档/废弃
 ┌──────────┐      ┌──────────┐     ┌──────────────┐     ┌──────────────┐
 │  main    │ ──→  │  main    │ ──→ │  worktree    │ ──→ │  main        │
 │          │      │          │     │  change/<id> │     │  合并/清理    │
 └──────────┘      └──────────┘     └──────────────┘     └──────────────┘
                                        ↑ 创建                 ↓ 删除
                               EnterWorktree            ExitWorktree +
                               branch: change/<id>      git merge +
                                                        git worktree remove
```

## Worktree 生命周期状态

| 状态 | 含义 | 触发时机 |
|------|------|---------|
| none | 无 worktree | 阶段 0-1（设计完成前） |
| active | worktree 已创建，agent 在其中工作 | 阶段 2 闸门通过后 |
| suspended | change 被中断，worktree 保留 | 中断流程 |
| cleaned | worktree 和分支已删除 | 归档/废弃完成 |

## 数据流

```
1. 创建 worktree（2-任务闸门后）
   main HEAD → git worktree add .claude/worktrees/<id> -b change/<id>
   → agent 进入 worktree（EnterWorktree）
   → per-change STATE.md 记录 worktree_path

2. 活跃工作（阶段 2~5）
   spec 工件 + 代码改动 → 全部在 worktree 中提交到 change/<id> 分支
   per-change STATE.md 更新 → 同步到 worktree 内的 .specs/<id>/STATE.md

3. 归档合并
   agent 退出 worktree（ExitWorktree）→ 回到 main
   git merge change/<id> → specs + 代码 合入 main
   解决 STATE.md 冲突（保留 main 版本，手动移除已归档 change 行）
   git worktree remove .claude/worktrees/<id>
   git branch -d change/<id>

4. 废弃清理
   agent 退出 worktree → 回到 main
   git worktree remove --force .claude/worktrees/<id>（不合并）
   git branch -D change/<id>
```

## 技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| Worktree 工具 | Claude Code EnterWorktree/ExitWorktree | 内建工具，自动管理目录和分支 |
| 分支命名 | `change/<id>` | 与 change-id 一致，清晰可追溯 |
| Worktree 路径 | `.claude/worktrees/<id>` | 组织在 .claude 目录下，避免污染项目根 |
| 生命周期定义 | `references/worktree-lifecycle.md`（新建） | 单一真相源，各阶段引用 |
| 回退方案 | Bash 调用 `git worktree` 命令 | EnterWorktree 不可用时手动操作 |

## ADR

### ADR-1: Worktree 路径位置

**背景**：worktree 目录放在哪里影响项目结构和 .gitignore 配置。

**选项**：
- (a) `.claude/worktrees/<id>` — 组织在 Claude 配置目录下
- (b) `../<id>-worktree` — 项目外上级目录
- (c) 系统 tmp 目录

**决策**：(a)

**理由**：集中管理，易于查找和清理；.claude 目录通常已在 .gitignore 中；不会产生与项目无关的目录。

### ADR-2: 分支命名规范

**背景**：需要一致的命名规范便于识别和清理。

**选项**：
- (a) `change/<id>` — 与 change-id 命名空间一致
- (b) `feature/<id>` — 常见 git 分支前缀
- (c) `flowgo/<id>` — flow-go 专属命名空间

**决策**：(a)

**理由**：change-id 是 flow-go 的核心概念，`change/` 前缀清晰表达"这是一个 flow-go change 的分支"，不会与用户的 feature/bugfix 分支混淆。

### ADR-3: STATE.md 合并策略

**背景**：归档合并时 STATE.md 可能有冲突（main 上的版本可能已被其他 change 更新）。

**选项**：
- (a) `.gitattributes merge=ours` — 自动保留 main 版本
- (b) 手动冲突解决 — 归档时 agent 显式处理
- (c) `.gitignore STATE.md` — 不追踪 STATE.md

**决策**：(b)

**理由**：不修改项目的 .gitattributes（非侵入式）；归档流程中 STATE.md 已有显式更新步骤（移除索引行），自然处理冲突；不丢失 STATE.md 的版本历史。

### ADR-4: LITE 复杂度也使用 worktree

**背景**：LITE 模式简化闸门，是否也简化 worktree？

**选项**：
- (a) LITE 跳过 worktree — 减少开销
- (b) LITE 也使用 worktree — 统一体验

**决策**：(b)

**理由**：用户明确要求"单个 change 也需要 worktree，因为中途可能插入新 change"。LITE change 同样面临中断和切换需求。

## 既有架构对齐

### 触碰模块
| 模块文件 | 变更类型 | 说明 |
|---------|---------|------|
| SKILL.md | 修改 | 步骤 1/3/7 增加 worktree 感知 |
| references/stages/2-task.md | 修改 | 闸门后增加 worktree 创建步骤 |
| references/stages/special-flows.md | 修改 | 归档/废弃/中断/回溯 增加 worktree 处理 |
| references/worktree-lifecycle.md | **新建** | 完整生命周期定义 |
| references/artifacts/spec-artifacts.md | 修改 | STATE.md 模板增加 worktree_path |

### 禁动清单
- 不改角色分工（步骤 5 角色声明不变）
- 不改闸门检查的严格程度逻辑
- 不改工件模板的核心结构（仅新增字段）
- 不改决策信号定义

### 沿用决策
- 沿用 per-change STATE.md 管理（步骤 7 已有机制）
- 沿用归档流程的索引更新机制（步骤 8）
- 沿用交叉评审子代理协议

## 风险清单

| 风险 | 概率 | 影响 | 缓解方案 |
|------|------|------|---------|
| 归档合并时 STATE.md 冲突 | 中 | 低 | ADR-3：agent 显式处理，保留 main 版本 |
| Worktree 磁盘占用累积 | 低 | 低 | 归档/废弃自动清理；归档维护流程扫描残留 |
| 用户手动切换分支导致 worktree 失效 | 低 | 中 | per-change STATE.md 记录 worktree_path，回溯时可恢复 |
| EnterWorktree 工具不可用 | 低 | 高 | 回退到 Bash 执行 git worktree 命令 |
| 并行 change 的 STATE.md 合并冲突 | 中 | 中 | 每个归档独立处理，顺序合并避免交叉冲突 |

## 范围控制

- 只增加 worktree 生命周期管理，不重构现有阶段逻辑
- 不引入新的配置项（沿用现有 .flowgo-config）
- 不实现 worktree 级别的依赖隔离
