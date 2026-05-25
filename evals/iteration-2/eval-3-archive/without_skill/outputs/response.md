# 归档 — user-auth

当前活跃 Change **user-auth** 处于 **5-审查** 阶段。

## 归档前检查

在归档之前，需要确认以下事项：

1. **审查阶段是否已完成？** — 当前处于 5-审查，归档通常意味着工作已完成。请确认：
   - 代码审查是否已通过？
   - 所有审查意见是否已处理？
   - 是否已合并到主分支？

2. **仓库状态是否干净？** — 需要确认 `git status` 无未提交变更。

## 归档操作

如果确认可以归档，我将执行以下步骤：

1. **收集工件** — 将 user-auth 的所有规格文件（REQUIREMENT.md、DESIGN.md、TASK.md、CHANGE.md、STATE.md、审查记录等）移动到 `.specs/archive/` 目录下，以 `user-auth` 命名。

2. **更新归档索引** — 在 `.specs/archive/ARCHIVE-INDEX.md` 中添加归档条目：
   - 归档目录：`user-auth`
   - Change-ID：`user-auth`
   - 完成阶段：`5-审查`
   - 归档日期：`2026-05-25`

3. **清理 STATE.md** — 将 STATE.md 重置为无活跃 Change 状态。

4. **验证** — 确认 `git status` 干净。

---

**请确认是否继续归档？** 如果审查阶段尚未完成，建议先完成审查再归档。如果这是一个提前终止的归档（废弃），请说明原因。
