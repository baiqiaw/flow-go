# DESIGN — change-pipeline

## 0. 技术栈选定

| 候选方案 | 优点 | 缺点 | 推荐 |
|---------|------|------|------|
| A. 单一 PIPELINE.md + per-change .lock 文件 | 与现有 Markdown 风格一致；锁随 change 走，归档自动清理 | 扫描所有锁需遍历目录 | **首选** |
| B. PIPELINE.md + 共享 .specs/locks/ 目录 | 锁集中管理，扫描快 | 锁与 change 解耦，归档时需额外清理 | 备选 |
| C. YAML pipeline + STATE.md 内嵌锁 | 结构化数据更易解析 | 打破纯 Markdown 约定；STATE.md 膨胀 | 排除 |

最终选择：**方案 A**，理由：REQUIREMENT 的 Key Decisions 已确定 PIPELINE.md 独立文件 + .lock 文件方案，与 flow-go 现有"纯文件驱动"风格一致，归档时 .lock 随 change 目录一起移动/清理，无需额外处理。

## 1. 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      SKILL.md (路由+状态)                      │
│  新增路由: 排队/pipeline/backlog                               │
│  新增字段: Pipeline 待续, 并行 Change                         │
│  步骤1 读状态: + 读 Pipeline 待续, 并行 Change                │
│  步骤7 状态更新: + PIPELINE.md 状态同步                       │
└──────────┬──────────────────────────────────────┬───────────┘
           │                                      │
     ┌─────▼─────┐                          ┌─────▼─────┐
     │ 0-需求     │                          │ 归档/中断  │
     │ (拆分联动) │                          │ (衔接流程) │
     └─────┬─────┘                          └─────┬─────┘
           │                                      │
     ┌─────▼──────────────────────────────────────▼─────┐
     │              .specs/PIPELINE.md                    │
     │  ┌──────┬──────┬──────┬──────┬──────┬──────┐      │
     │  │ id   │ 描述 │ 优先 │ 依赖 │ 状态 │ 范围 │      │
     │  ├──────┼──────┼──────┼──────┼──────┼──────┤      │
     │  │ ch-1 │ ...  │ M    │ -    │act.  │ **   │      │
     │  │ ch-2 │ ...  │ S    │ ch-1 │pend. │ **   │      │
     │  └──────┴──────┴──────┴──────┴──────┴──────┘      │
     └───────────┬──────────────────────┬────────────────┘
                 │                      │
        ┌────────▼────────┐    ┌────────▼────────┐
        │ .specs/ch-1/    │    │ .specs/ch-2/    │
        │ ┌─── CHANGE.md  │    │ ┌─── CHANGE.md  │
        │ ├─── REQ.md     │    │ ├─── REQ.md     │
        │ └─ .lock ← NEW  │    │ └─ ...          │
        └─────────────────┘    └─────────────────┘
```

## 2. 数据流

**Flow 1: 拆分创建**
```
0-需求 步骤2 检测多子系统
  → 用户确认拆分
  → 创建 PIPELINE.md，写入 N 个 change（第 1 个 active，其余 pending）
  → 当前 change 继续 0-需求后续步骤
```

**Flow 2: 归档衔接**
```
归档步骤9 STATE.md 清空前
  → 检查 PIPELINE.md 是否有 pending change
  → 找到下一个（优先级排序 + 依赖检查）
  → STATE.md 写入 Pipeline 待续 字段
  → 输出提示 + 询问用户
  → 用户确认 → 启动新 change
  → 用户拒绝 → 保留 Pipeline 待续 字段
```

**Flow 3: 中断（新流程，替代直接归档）**
```
用户请求暂停/切换 change
  → PIPELINE.md 中状态改为 interrupted
  → STATE.md 中断任务 记录中断阶段
  → .specs/<id>/ 目录和工件保持不动
  → STATE.md 活跃 Change 可清空（允许多任务）
```

**Flow 4: 恢复**
```
新会话启动 / 用户说"继续"
  → STATE.md 活跃 Change 为空
  → 检查 Pipeline 待续 字段 → 有则提示
  → 否则扫描 .specs/ 非 archive 目录 → 列出可选恢复项
  → 用户选择 → 恢复到中断阶段
```

**Flow 5: 并行启动**
```
用户请求并行
  → 检查新 change 文件范围是否与现有 active change 重叠
  → 无冲突 → PIPELINE.md 标记为 active
  → STATE.md 并行 Change 字段追加
  → 冲突 → 建议串行或调整范围
```

**Flow 6: 任务锁**
```
3-开发 进入某任务
  → 创建 .specs/<id>/.lock（文件路径 + 任务ID + 时间戳）
  → 另一 agent 检查 → 锁冲突 → 阻止
  → 任务完成 → 删除 .lock
```

## 3. API 设计

不适用 REST/RPC API。内部文件读写协议：

| 操作 | 输入 | 输出 | 使用场景 |
|------|------|------|---------|
| 读 PIPELINE.md | 无 | 解析 Markdown 表格 → 结构化数据 | 排队管理、衔接检查 |
| 写 PIPELINE.md | change-id + 新状态 | 更新特定行状态 → 写回 | 状态变更（active/completed/interrupted） |
| 创建 PIPELINE.md | N 个 change 列表 | Markdown 表格文件 | 拆分时创建 |
| 读 .lock | change-id | JSON 对象 | 锁检查 |
| 写 .lock | files + task_id | JSON 文件 | 任务开始 |
| 删 .lock | change-id | 删除文件 | 任务完成 |
| 读 STATE.md 新字段 | 无 | Pipeline 待续 + 并行 Change 值 | 状态读取 |
| 写 STATE.md 新字段 | 字段名 + 值 | 更新字段 | Pipeline 衔接/并行启动 |

## 4. ADR

### ADR-001 PIPELINE.md 独立文件 vs STATE.md 字段
- 背景：需要记录多个 change 的排队信息
- 选项：A) 独立 PIPELINE.md；B) 在 STATE.md 中嵌入
- 决策：独立文件
- 理由：STATE.md 是单 change 状态指针，pipeline 是多 change 编排，职责不同。PIPELINE.md 可能包含数十行记录，嵌入会使 STATE.md 膨胀

### ADR-002 .lock 文件位置：per-change vs 共享目录
- 背景：需要记录任务正在改动的文件
- 选项：A) `.specs/<id>/.lock`（per-change）；B) `.specs/locks/<id>.lock`（共享目录）
- 决策：per-change
- 理由：锁随 change 目录走，归档时自动清理。共享目录需要额外的清理步骤，且与 change 的目录隔离原则冲突

### ADR-003 冲突检测：文件 glob 声明 vs 运行时检测
- 背景：并行 change 间需要检测文件冲突
- 选项：A) upfront 声明 glob 模式；B) 运行时检测实际改动文件
- 决策：glob 声明
- 理由：运行时检测需要文件系统 hook 或 diff 分析，复杂度高。glob 声明虽可能有误报（路径包含但实际不冲突），但实现简单且安全（宁可拒绝也不允许冲突）

### ADR-004 中断状态：PIPELINE.md 标记 vs STATE.md 标记
- 背景：change 未走完流程需要暂停
- 选项：A) 仅在 PIPELINE.md 标记 interrupted；B) 仅在 STATE.md 标记；C) 双重标记
- 决策：双重标记
- 理由：PIPELINE.md 是完整数据源（有所有 change 的状态），STATE.md 是快速入口（当前活跃状态）。恢复时先查 STATE.md，再查 PIPELINE.md 详情。双重标记确保任一入口都能获取完整信息

### ADR-005 锁粒度：任务级文件 vs change 级
- 背景：并行执行时需要锁防止冲突
- 选项：A) 锁定整个 change；B) 锁定任务声明的具体文件
- 决策：任务级文件锁
- 理由：change 级锁太粗（一个 change 可能涉及 10 个文件但只改其中 2 个），任务级锁允许同一 change 的不同任务并行执行，只要文件不重叠

## 5. 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| R1. 多 agent 同时写 PIPELINE.md 导致数据丢失 | 中 | 高 | PIPELINE.md 为单 agent 编辑模式（一个会话只有一个主 agent），多 agent 场景通过 .lock 互斥；写入前读取最新内容 |
| R2. 会话崩溃导致 .lock 残留 | 中 | 中 | 回溯流程增加"残留锁检测"步骤：扫描 .specs/ 下所有 .lock 文件，检查对应任务是否仍有 SUMMARY（已完成的锁视为残留，提示删除） |
| R3. glob 模式误报导致不必要的串行 | 低 | 低 | 用户可在 PIPELINE.md 中调整 glob 范围；误报只影响效率不影响正确性 |
| R4. STATE.md 格式迁移破坏现有项目 | 低 | 高 | 格式迁移仅限本 change 的 STATE.md；回溯流程增加"STATE.md 格式兼容性检查"，旧格式自动识别并升级 |
| R5. Pipeline 积压过多 change | 低 | 低 | 排队管理命令支持跳过和调整优先级；归档维护流程可清理已不需要的 pending change |

## 6. 既有架构对齐

- 触碰模块：SKILL.md（路由表 + 状态读写 + 状态更新）、stages/0-requirement.md（拆分步骤 + 文件范围声明）、stages/3-develop.md（锁机制）、stages/special-flows.md（归档衔接 + 中断流程 + 回溯增强）、artifacts/meta-artifacts.md（STATE.md schema + PIPELINE/.lock 模板）
- 禁动清单：其他 6 个阶段文件、cross-review-matrix.md、sync-workflow.md、Python 脚本、闸门检查表
- 沿用决策：纯文件驱动（Markdown + JSON）、渐进增强（PIPELINE.md 不存在时静默跳过）、用户确认制（衔接仅提示不自动执行）、目录结构约定（.specs/<id>/ 隔离边界）

## 7. 修改点清单

### 7.1 SKILL.md

| 位置 | 修改内容 | 对应 AC |
|------|---------|---------|
| 路由表（第三步） | 新增行：`排队` / `pipeline` / `backlog` → 排队管理 | AC-5 |
| 步骤1 第3点 | `Pipeline 待续` 非空 → 优先提示 pipeline 衔接 | AC-8.1 |
| 步骤1 第3点 | `并行 Change` 非空 → 展示并行状态 | AC-11 |
| 步骤7 | 归档完成后新增 Pipeline 衔接检查（在 STATE.md 清空前） | AC-3, AC-7 |
| 步骤7 | 中断流程：STATE.md 写入 `中断任务`，PIPELINE.md 更新状态 | AC-9 |

### 7.2 stages/0-requirement.md

| 位置 | 修改内容 | 对应 AC |
|------|---------|---------|
| 步骤2（多子系统检测） | 用户确认拆分后：创建 `.specs/PIPELINE.md`，写入 N 个 change | AC-1 |
| 步骤2 新增子步骤 | 每个拆分出的 change 要求声明 `文件范围`（glob 模式） | AC-12 |
| 步骤2 新增子步骤 | 拆分时进行 `依赖` 声明（change 间依赖关系） | AC-6 |
| 输出 | 新增 `.specs/PIPELINE.md`（如触发拆分） | AC-1 |

### 7.3 stages/3-develop.md

| 位置 | 修改内容 | 对应 AC |
|------|---------|---------|
| 任务开始前 | 新增锁检查：读 `.specs/<id>/.lock`，如存在且非当前任务 → 阻止 | AC-13, AC-15 |
| 任务开始时 | 新增锁创建：写 `.specs/<id>/.lock`（files + task_id + timestamp） | AC-14 |
| 任务完成时 | 新增锁释放：删除 `.specs/<id>/.lock` | AC-14 |

### 7.4 stages/special-flows.md

| 位置 | 修改内容 | 对应 AC |
|------|---------|---------|
| 归档步骤（步骤5-9 之间） | 新增 Pipeline 衔接检查：步骤9 前检查 pending → 写入 Pipeline 待续 → 提示 | AC-3, AC-7 |
| 归档步骤 9 | STATE.md 清空保留 `Pipeline 待续` 字段（如有的话） | AC-3 |
| 新增「中断」流程 | 用户请求暂停 → PIPELINE.md interrupted → STATE.md 记录 → 工件保留 | AC-9 |
| 回溯步骤 | 新增 Pipeline 待续 检查 + 残留锁检测 | AC-8.1, R2 |
| 回溯步骤 | 新增：STATE.md 活跃 Change 为空时扫描 .specs/ 未归档目录 | AC-10 |

### 7.5 artifacts/meta-artifacts.md

| 位置 | 修改内容 | 对应 AC |
|------|---------|---------|
| STATE.md Schema | 新增 `Pipeline 待续` 和 `并行 Change` 字段定义 | AC-3, AC-11 |
| STATE.md 格式约束 | 更新字段数 5 → 7，新增字段校验规则 | — |
| STATE.md 完整性校验 | 新增 `Pipeline 待续` 和 `并行 Change` 存在性检查 | — |
| STATE.md 模板 | 更新为新格式（Markdown 标题+列表） | — |
| 新增 PIPELINE.md 模板 | 完整的 Markdown 表格模板 + 格式约束 | AC-2 |
| 新增 .lock 文件模板 | JSON 格式模板 + 格式约束 | AC-13, AC-14 |

## 8. PIPELINE.md 详细格式

```markdown
# PIPELINE — change 排队记录

| change-id | 描述 | 优先级 | 依赖 | 状态 | 文件范围 | 备注 |
|-----------|------|--------|------|------|----------|------|
| change-pipeline | Pipeline 排队机制 | MustHave | - | active | SKILL.md,references/** | 当前 change |
| evolution-enhance | 进化分析增强 | ShouldHave | change-pipeline | pending | references/scripts/** | 依赖 pipeline 归档 |
```

**状态枚举**：`active` | `pending` | `completed` | `skipped` | `interrupted`

**格式约束**：
1. 文件编码 UTF-8，首行 `# PIPELINE — change 排队记录`
2. 表格为标准 Markdown 表格，列顺序固定（7 列）
3. `依赖` 列为 change-id（逗号分隔多个），无依赖写 `-`
4. `文件范围` 列为 glob 模式（逗号分隔），如 `src/auth/**,src/api/login.py`
5. `状态` 列仅取 5 个枚举值之一
6. 允许同一 PIPELINE.md 中有多个 `active`（并行场景）

## 9. .lock 文件格式

路径：`.specs/<id>/.lock`

```json
{
  "task_id": "T01",
  "files": ["src/api.py", "src/auth/login.py"],
  "agent_id": "agent-1",
  "timestamp": "2026-05-20T14:30:00Z"
}
```

**约束**：
1. JSON 格式，一个 change 目录下最多一个 `.lock` 文件
2. `files` 列表为任务声明改动的具体文件路径（非 glob，是实际路径）
3. `agent_id` 用于区分多 agent 场景（可选，默认 `"default"`）
4. 任务 SUMMARY.md 产出后删除 `.lock`
5. 归档时 `.lock` 随目录移动到 archive/，自然清理

## 10. STATE.md 变更

新增 2 个字段：

| 字段 | 位置 | 格式 | 说明 |
|------|------|------|------|
| `Pipeline 待续` | 在 `中断任务` 之后 | `<change-id>` 或 `无` | 归档衔接时写入，用户确认启动后清空 |
| `并行 Change` | 在 `Pipeline 待续` 之后 | `<id1>,<id2>` 或 `无` | 并行活跃 change 列表（逗号分隔） |

更新后完整字段（7 个）：

```markdown
# STATE — flow-go 项目状态

## 活跃 Change
- change-pipeline

## 当前阶段
- 1-设计

## 当前任务
- 无

## 中断任务
- 无

## Pipeline 待续
- 无

## 并行 Change
- 无

## 阶段进度
- 步骤 3: 架构确认完成，设计中

## 更新时间
- 2026-05-20
```
