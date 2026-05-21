# CHANGE — worktree-isolation

## 概述
为 flow-go 增加 git worktree 隔离机制：每个 change 在设计完成后自动创建独立 worktree，归档时合并回 main 并清理 worktree，确保并行 change 互不干扰、git 历史清晰、仓库干净。

## 类型
config（流程配置优化）

## 动机
四大痛点：
1. **多 change 互相干扰**：并行开发时多个 change 的代码改动互相影响，难以隔离
2. **中途插入新 change**：即使只有一个活跃 change，中途可能需要插入热修或新需求，worktree 让 main 随时可切换
3. **git 历史混乱**：所有 change 都在 main 上直接提交，历史不清晰，难回溯
4. **废弃 change 难清理**：放弃的 change 留下一堆未提交改动，不知道哪些该保留

## 用户故事
作为 flow-go 用户，我希望每个 change 都在独立的 git worktree 中工作，这样我可以：
- 同时进行多个 change 而互不干扰
- 随时废弃一个 change 而不影响其他工作
- 归档后获得干净的 git 历史和仓库状态

## 影响面
- 涉及 flow-go skill 的核心流程（SKILL.md + stages + special-flows）
- 改变归档/废弃流程的步骤
- 影响 STATE.md 管理（worktree 上下文追踪）
- 不影响现有工件模板

## 范围排除
- 不改变 flow-go 的角色分工和闸门检查逻辑
- 不实现跨仓库的 worktree 管理（仅限单仓库）
- 不实现 worktree 内部的依赖隔离（如 node_modules）
