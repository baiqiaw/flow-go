# Flow-Go 废弃流程

## 第一步 · 读状态

读取 STATE.md（旧格式检测）：

STATE.md 中 `## 活跃 Change` 下为非表格的单行文本（`- legacy-api`），判定为**旧格式**。执行旧格式迁移。

🔄 旧格式 STATE.md 已自动迁移为新格式。

迁移后的 STATE.md（新格式）：

```markdown
# STATE.md — flow-go 状态文件

## 活跃 Change

| change-id | 阶段 | 最后更新 |
|-----------|------|---------|
| legacy-api | 1-设计 | 2026-05-15 |

## Pipeline 待续
- 无

## 更新时间
- 2026-05-15
```

同时创建 `.specs/legacy-api/STATE.md`（change 级详情）：

```markdown
# STATE.md — change: legacy-api

## 当前阶段
- 1-设计

## 路径模式
- 完整

## 当前任务
- 无

## 中断任务
- 无

## 阶段进度
- 步骤 3: 技术栈选型进行中

## 更新时间
- 2026-05-15
```

活跃 Change 数 = 1，自动读取 `.specs/legacy-api/STATE.md`：
- change-id: `legacy-api`
- 路径模式: `完整`
- 当前阶段: `1-设计`
- 当前任务: 无
- 中断任务: 无
- 阶段进度: 步骤 3: 技术栈选型进行中

中断任务为空，不触发回溯。
Worktree 检查：`worktree_path` 字段不存在，跳过。

## 第二步 · 加载配置

无 `.flowgo-config` 文件，使用内置默认值。

## 第三步 · 意图路由

用户输入："废弃这个需求"

路由表匹配：
| 用户输入特征 | 路由到 |
|---|---|
| `废弃` / `放弃` / `abandon` / `cancel` | 废弃流程 |

**命中：废弃流程 → 角色：项目经理**

## 第四步 · 闸门检查

废弃流程闸门：用户显式确认废弃（必须确认）。

废弃影响评估：

**已到达阶段**：1-设计（步骤 3: 技术栈选型进行中）
**代码状态**：尚未进入开发阶段，无代码提交
**并行依赖**：无并行 Change

---

⚠️ **废弃确认**

即将废弃 `legacy-api`（当前阶段：1-设计，步骤 3: 技术栈选型进行中）

影响评估：
- 已到达阶段：0-需求 ✅（推测，因已进入 1-设计）→ 1-设计（未完成，步骤 3 进行中）
- 代码提交：无（尚未进入开发阶段）
- 并行依赖：无
- 已有工件：可能在 `.specs/legacy-api/` 下有部分设计工件

**确认废弃？**（回复"确认"继续）

---

假设用户确认废弃，继续执行以下步骤：

## 第五步 · 角色声明

```
✅ 路由：废弃流程
✅ Change-ID：legacy-api
✅ 路径模式：完整
✅ 复杂度：STANDARD
✅ 当前角色：项目经理
✅ 角色红线：评估废弃影响并执行，不改代码
✅ 阶段锚点：（废弃流程无锚点口诀）
✅ 第一动作：写 ABANDONED.md，移动归档
✅ 项目记忆：无
```

## 第六步 · 执行废弃流程

### 步骤 1 — 确认废弃目标

用户未指定 change-id → 取 STATE.md 索引表的活跃 Change → `legacy-api`

### 步骤 2 — 废弃影响评估

已列出（见上方闸门检查部分）：
- 已到达阶段：1-设计（步骤 3 进行中，未完成）
- 代码提交状态：无代码提交（尚未进入开发阶段）
- 并行依赖：无并行 Change

### 步骤 3 — 写 ABANDONED.md

在 `.specs/legacy-api/` 下创建 `ABANDONED.md`：

```markdown
# ABANDONED — legacy-api

## 废弃原因
用户主动废弃（具体原因未指定）

## 已到达阶段
- 0-需求 ✅
- 1-设计 ⬜（步骤 3: 技术栈选型进行中，未完成）

## 已有工件
| 文件 | 状态 |
|------|------|
| CHANGE.md | ⬜ 未确认 |
| REQUIREMENT.md | ⬜ 未确认 |
| DESIGN.md | ⬜ 未确认（设计中） |

## 代码状态
- 是否有已提交代码：否
- 如有，涉及的分支/commit：不适用

## 可复用资产
- 需求分析（如 REQUIREMENT.md 存在）
- 技术栈选型的部分研究成果（步骤 3 进行中）

## 废弃时间
2026-05-25
```

### 步骤 4 — 临时文件清理

扫描 `.specs/legacy-api/` 下所有 `*-PROGRESS.md` 文件 → 无（设计中阶段通常不产出 PROGRESS 文件）。

`user-inputs.jsonl` 不删除，随目录移动到归档。

### 步骤 4.5 — Worktree 清理

`.specs/legacy-api/STATE.md` 中 `worktree_path` 字段不存在 → 跳过。

### 步骤 5 — 移动归档

```
mv .specs/legacy-api/ .specs/archive/abandoned/2026-05-25-legacy-api/
```

### 步骤 6 — 更新归档索引

创建 `.specs/archive/ARCHIVE-INDEX.md`：

```markdown
# ARCHIVE INDEX — 归档索引

> 归档时自动维护，回溯时可选读取。不需要手动编辑。

## 归档统计
- 正常归档：0 个
- 废弃归档：1 个
- 最近归档：2026-05-25-legacy-api
- 最早归档：2026-05-25-legacy-api

## 归档清单

### 正常完成
| 归档目录 | Change-ID | 完成阶段 | 归档日期 | 保留状态 |
|----------|-----------|---------|---------|---------|
| （无） |

### 废弃
| 归档目录 | Change-ID | 废弃原因 | 归档日期 | 保留状态 |
|----------|-----------|---------|---------|---------|
| 2026-05-25-legacy-api | legacy-api | 用户主动废弃 | 2026-05-25 | 保留 |

## 清理策略
- 默认保留期限：90 天
- 超期标记：`保留状态` 列标记为"可清理"
```

### 步骤 7 — STATE.md 清理

废弃的是活跃 Change → 从索引表移除该 change 行 + 删除 `.specs/legacy-api/STATE.md`

更新后的 STATE.md（项目级）：

```markdown
# STATE.md — flow-go 状态文件

## 活跃 Change

| change-id | 阶段 | 最后更新 |
|-----------|------|---------|
| | | |

## Pipeline 待续
- 无

## 更新时间
- 2026-05-25
```

### 步骤 8 — LESSONS 提名

扫描 PROGRESS 文件 → 无 PROGRESS 文件（设计阶段未完成）→ 无 LESSONS 提名。

### 步骤 9 — outcome 标记

`.specs/traces.jsonl` 不存在 → 跳过。

## 第七步 · 状态更新

STATE.md 已更新：
- 索引表中 `legacy-api` 行已移除
- `.specs/legacy-api/STATE.md` 已删除（随目录移动到归档）
- 更新时间更新为 2026-05-25

决策同步检查：废弃不产生决策，跳过。

自动进化检查：废弃不触发进化分析。

## 废弃完成

**废弃摘要**：

```
🗑️ legacy-api 已废弃

- 废弃原因：用户主动废弃
- 已到达阶段：1-设计（步骤 3 进行中）
- 代码提交：无
- 归档位置：.specs/archive/abandoned/2026-05-25-legacy-api/
- ABANDONED.md 已写入
- STATE.md 已清理（活跃 Change 表为空）
- 归档索引已更新

当前状态：无活跃 Change。可随时开始新需求。
```

## 自检

- [x] 废弃目标已确认（legacy-api）
- [x] 影响评估已输出（阶段进度 + 代码状态 + 依赖检查）
- [x] ABANDONED.md 已写入
- [x] PROGRESS.md 已清理（无 PROGRESS 文件需清理）
- [x] 归档索引已更新（ARCHIVE-INDEX.md 已创建）
- [x] STATE.md 已更新（索引表已移除 legacy-api 行 + .specs/legacy-api/STATE.md 已随目录归档）
- [x] worktree 已清理（不适用，无 worktree）
