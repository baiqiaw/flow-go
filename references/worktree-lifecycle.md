# Worktree 生命周期

> 本文档定义 flow-go 中 git worktree 隔离机制的完整生命周期。SKILL.md 路由后按流程名 grep 加载。

---

## 概述

flow-go 为每个 change 提供独立 git worktree，实现以下目标：

- **代码隔离**：change 的所有文件改动和 git 提交都在独立 worktree 中进行，主仓库 working tree 不受影响
- **历史清晰**：每个 change 对应 `change/<id>` 分支，提交历史独立可追溯
- **易于清理**：归档或废弃时，删除 worktree 和分支即可回收资源

**适用范围**：flow-go 管理的所有 change，包括 LITE 复杂度。

**核心原则**：per-change STATE.md 的 `worktree_path` 字段是 worktree 状态的唯一真相源。

---

## 生命周期状态

| 状态 | 含义 | 判定方式 |
|------|------|---------|
| none | 无 worktree | per-change STATE.md 的 `worktree_path` 为 `无` |
| active | worktree 已创建 | `worktree_path` 非空且目录存在 |
| suspended | change 中断，worktree 保留 | `worktree_path` 非空且中断任务非空 |
| cleaned | 已清理 | `worktree_path` 为 `无`（从 active/suspended 转换） |

**状态转换图**：

```
none → active → cleaned
           ↓           ↑
      suspended ──────┘
```

---

## 创建流程（AC-1）

**触发时机**：0-需求阶段步骤 3.5（change-id 生成后立即创建）。

**前置条件**：per-change STATE.md 的 `worktree_path` 为 `无`。

**步骤**：

1. 调用 `EnterWorktree`（name: `<change-id>`），创建分支 `change/<id>` 的 worktree，路径为 `.claude/worktrees/<id>`
2. 进入 worktree 后，创建 `.specs/<id>/` 目录，将 REQUIREMENT.md / CHANGE.md 写入
3. 创建 `.specs/<id>/STATE.md`，`worktree_path` 写入 worktree 绝对路径
4. 在 worktree 中验证：`git branch --show-current` 输出 `change/<id>`

**回退方案**：`EnterWorktree` 不可用时，用 Bash 执行：

```bash
git worktree add .claude/worktrees/<id> -b change/<id>
```

然后手动 cd 到 worktree 目录。

**跳过条件**：`worktree_path` 已有值 → agent 已在 worktree 中，无需重复创建。

---

## 活跃工作（AC-2）

**适用阶段**：0-需求（步骤 3.5 之后）、1-设计、2-任务、3-开发、4-测试、5-审查、6-部署。

**行为规则**：

- agent 在 worktree 中操作，所有文件改动和 git 提交都在 worktree 中进行
- per-change STATE.md 在 worktree 内更新（改动提交到 `change/<id>` 分支）
- 主仓库 working tree 不受影响
- 工件文件（SUMMARY、PROGRESS、TEST、REVIEW 等）在 worktree 的 `.specs/<id>/` 下创建和编辑

---

## 归档合并流程（AC-3、AC-4、AC-6）

**前置条件**：change 进入归档流程且 `worktree_path` 非空。

**步骤**：

1. `ExitWorktree` 退出 worktree，回到主仓库
2. `git checkout main` 确保在 main 分支
3. `git merge change/<id>` 将分支合并到 main
4. **STATE.md 冲突处理**：接受 main 版本（`git checkout --ours .specs/<id>/STATE.md`），然后 agent 手动执行归档流程中的 STATE.md 清理步骤（移除已归档 change 行）
5. **其他冲突**：停下来提示用户手动解决，不允许自动合并
6. `git worktree remove .claude/worktrees/<id>` 删除 worktree
7. `git branch -d change/<id>` 删除分支
8. per-change STATE.md 的 `worktree_path` 清为 `无`（已在归档流程中处理）

**合并后验证**：

- `git status` 显示 clean
- `git worktree list` 仅显示主仓库

---

## 废弃清理流程（AC-5、AC-6）

**前置条件**：change 被废弃且 `worktree_path` 非空。

**步骤**：

1. `ExitWorktree` 退出 worktree
2. `git worktree remove --force .claude/worktrees/<id>` 强制删除（丢弃所有未合并改动）
3. `git branch -D change/<id>` 强制删除分支（不合并）

**清理后验证**：

- `git worktree list` 仅显示主仓库

---

## 中断处理

**触发时机**：change 被中断（用户说"中断/暂停/interrupt"）。

**行为规则**：

- worktree 保留不删除，状态自然转为 suspended
- per-change STATE.md 保留 `worktree_path`（不清空）
- 中断任务字段记录中断阶段（如 `3-开发/T02`）
- worktree 中的代码改动和 git 历史完整保留，恢复时可继续

---

## 回溯恢复（AC-7）

**触发时机**：用户请求恢复（回溯/继续）一个有 worktree 的 change。

**步骤**：

1. 读取 per-change STATE.md 的 `worktree_path`
2. `worktree_path` 非空 → 检查 `test -d <path>`
3. 目录存在 → `EnterWorktree`（path: `<path>`）进入
4. 目录不存在 → 输出「worktree 已丢失：<path>，建议手动恢复或废弃该 change」
5. `worktree_path` 为 `无` → 留在主仓库（0-需求步骤 3.5 之前尚未创建 worktree 的状态）

**恢复后验证**：

- `git branch --show-current` 输出 `change/<id>`
- worktree 内 `.specs/<id>/` 目录存在
