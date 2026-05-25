# Flow-Go 响应

## 第一步 · 读状态

读取项目根目录 `STATE.md`：

```markdown
# STATE

活跃 Change: user-auth
当前阶段: 3-开发
当前任务: T02
中断任务:

最后更新: 2026-05-14
```

### 旧格式检测与迁移

STATE.md `活跃 Change` 字段为非表格的单行文本（`user-auth`），非 `无`。判定为**旧格式**。

执行迁移：

**(a) 读取旧格式所有字段**：
- 活跃 Change: user-auth
- 当前阶段: 3-开发
- 当前任务: T02
- 中断任务: （空）
- Pipeline 待续: （空）
- 并行 Change: （空）
- 更新时间: 2026-05-14

**(b) 生成新格式 STATE.md**（项目级索引表）：

```markdown
# STATE

## 活跃 Change

| change-id | 阶段 | 最后更新 |
|-----------|------|---------|
| user-auth | 3-开发 | 2026-05-14 |

## Pipeline 待续

无

最后更新: 2026-05-14
```

**(c) 创建 `.specs/user-auth/STATE.md`**：

```markdown
# STATE

change-id: user-auth
当前阶段: 3-开发
当前任务: T02
中断任务:
路径模式: 待确定
阶段进度:

最后更新: 2026-05-14
```

旧格式 `并行 Change` 字段为空，无需迁移为多行。

🔄 旧格式 STATE.md 已自动迁移为新格式。

### 完整性校验

运行 `validate_state.py`：
- 项目级 STATE.md 索引表格式正确（1 个活跃 change）
- `.specs/user-auth/STATE.md` 字段完整
- 校验通过

### 解析活跃 Change

活跃数 = 1 → 自动读取 `.specs/user-auth/STATE.md`：
- change-id: user-auth
- 当前阶段: 3-开发
- 路径模式: 待确定（旧格式迁移，路径模式未记录）
- 当前任务: T02
- 中断任务: （空）

中断任务为空 → 无需走回溯流程。

### Worktree 检查

`.specs/user-auth/STATE.md` 的 `worktree_path` 字段为空 → 留在主仓库。

### CONTEXT.md 检查

`.specs/CONTEXT.md` 不存在 → 棕地项目提醒：可运行 intel-scan 建立项目术语表，不强制。

---

## 第二步 · 加载配置

项目级 `.flowgo-config` 不存在。用户级 `~/.flowgo-config` 不存在。使用内置默认值。

---

## 第三步 · 意图路由

用户输入：`go`

路由表匹配：`go` / `下一步` / `next` → STATE 有活跃变更 → 读 per-change STATE 获取当前阶段和路径模式 → 按路径模式阶段转换表确定下一阶段。

当前阶段：3-开发。路径模式：待确定。

**路径模式缺失处理**：由于旧格式迁移，路径模式字段未记录。需要从已有工件推断：
- 检查 `.specs/user-auth/` 下是否存在 DESIGN.md、TASK.md 等工件
- 如存在完整工件链（REQUIREMENT + DESIGN + TASK）→ 路径模式为"完整"
- 如仅部分存在 → 根据实际工件推断

`.specs/user-auth/` 目录为空（旧格式迁移，工件未在 .specs 下保存），无法推断路径模式。

**降级策略**：默认使用"完整"路径模式。完整路径的阶段序列为：0→1→2→3→4→5→6→7。当前已在阶段 3-开发，用户说 "go" 意味着继续当前阶段的工作。

---

## 第三步半 · 复杂度分级

`complexity_classifier.py` 需要用户描述和项目目录，当前为会话恢复场景，无法自动分类。默认 **STANDARD**。

---

## 第四步 · 闸门检查

### 3-开发 阶段入口闸门

检查前置条件（完整路径模式）：

| 前置工件 | 状态 | 说明 |
|---------|------|------|
| DESIGN.md | ⚠️ 未确认 | 旧格式迁移，工件位置待确认 |
| TASK.md（含 verify） | ⚠️ 未确认 | 同上 |
| `<change-id>-REVIEW.md`（任务评审 PASS） | ⚠️ 未确认 | 同上 |
| T02 任务存在且 depends_on 已完成 | ⚠️ 未确认 | 需要读取 TASK.md |

**闸门结果**：由于旧格式迁移后 `.specs/user-auth/` 目录为空，无法验证前置工件是否存在。

**停下引导**：当前 change `user-auth` 从旧格式迁移而来，`.specs/user-auth/` 下没有工件文件。请确认：
1. 工件文件（REQUIREMENT.md / DESIGN.md / TASK.md 等）存放在哪里？
2. 是否需要将这些工件复制到 `.specs/user-auth/` 目录？
3. 或者，这是否是一个全新的 start（需要从 0-需求 阶段重新开始）？

---

## 第五步 · 角色声明

```
✅ 路由：3-开发
✅ Change-ID：user-auth
✅ 路径模式：完整（默认，待确认）
✅ 复杂度：STANDARD
✅ 当前角色：开发员
✅ 角色红线：不改 REQUIREMENT / DESIGN，每行改动追溯到需求
✅ 阶段锚点：每行改动追溯到需求
✅ 第一动作：确认工件位置，补齐前置条件后继续 T02 开发
✅ 项目记忆：无
```

---

## 第六步 · 加载执行

阶段文件：`references/stages/3-develop.md`
工件模板：`references/artifacts/task-artifacts.md`

### 3-开发 · 开发员角色激活

当前任务：**T02**

#### 会话恢复入口

1. 检查 `T02-PROGRESS.md` → 不存在（`.specs/user-auth/` 为空）
2. 检查最近 `*-SUMMARY.md` → 不存在
3. 两者都不存在 → **从步骤 1（读任务定义）开始**

#### 待执行步骤

由于前置工件（TASK.md / DESIGN.md 等）缺失，开发流程暂时无法继续。需要用户确认：

1. **如果工件存在于其他位置**：请提供文件路径，我将读取并继续 T02 开发
2. **如果需要重新开始**：建议从 0-需求 阶段重新走流程，生成完整的工件链
3. **如果仅需恢复 T02**：提供 TASK.md 内容即可开始开发

#### 开发步骤预览（工件就绪后执行）

1. 读 TASK.md 中 T02 任务定义，有歧义就反问
2. LESSONS 前置提醒（AC-7）
3. 策略复用（可选）
4. 前置健康检查：运行 linter/typecheck/test 确认基线
5. grep 沿用既有抽象
6. 扫 LESSONS.md
7. 锁检查
8. TDD：RED → GREEN → REFACTOR
9. 跑 verify（0 失败）
10. 提交前 diff 边界检查
11. 写 SUMMARY.md
12. 锁释放
13. 交叉评审（独立子代理）
14. 原子提交

---

## 第七步 · 状态更新

当前阶段未发生变化（仍在 3-开发），无需更新状态。待工件确认后继续执行。

---

## 自检

- [x] 已读 STATE.md
- [x] 已按路由表匹配意图（`go` → 当前阶段继续）
- [x] 已读取路径模式（旧格式迁移，默认"完整"，待确认）
- [x] 闸门前置条件已验证（发现工件缺失，已停下引导）
- [x] 角色声明包含红线提醒
- [ ] 决策同步检查：待阶段执行完成后进行
