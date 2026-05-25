# Pipeline 衔接与启动

检查并启动 Pipeline 中的下一个 change。

## 参数

- `{trigger}`：触发场景
  - `archive-complete`：归档完成后，从 PIPELINE.md 查找下一个 pending change
  - `recall-start`：回溯或读状态时，检查已有的 Pipeline 待续字段

## 前置条件

调用方须在调用前确保：

- `archive-complete`：已完成 PIPELINE.md pending 查找，`Pipeline 待续` 字段已写入 STATE.md
- `recall-start`：STATE.md 的 `Pipeline 待续` 字段非空 **且** 活跃 Change 表为空

## 步骤

1. 输出提示：「📋 Pipeline 待续：{change-id}，要开始吗？」
2. 询问用户是否立即开始
3. **用户确认** → 执行启动流程：
   - (a) 清空 STATE.md 的 `Pipeline 待续` 字段
   - (b) `.specs/PIPELINE.md` 中该 change 标记为 `active`
   - (c) 创建 `.specs/<id>/` 目录
   - (d) 创建 `.specs/<id>/STATE.md`（初始阶段：0-需求，当前任务：无）
   - (e) STATE.md 索引表新增该 change 行
   - (f) 路由到 0-需求阶段
4. **用户拒绝** → 保留 `Pipeline 待续` 字段，跳过

## archive-complete 特有前置步骤

（仅 `{trigger}=archive-complete` 时执行，在调用本流程之前完成）

- 读取 `.specs/PIPELINE.md`（如存在），找下一个 `pending` change（按优先级排序，依赖已完成）
- 找到 → 项目级 STATE.md 写入 `Pipeline 待续` 字段
- 找到 → 输出「📋 Pipeline 下一个：{change-id} — {描述}」
- PIPELINE.md 不存在或无 pending → 跳过整个衔接流程
