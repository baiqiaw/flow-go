# CHANGE — worktree-first-isolation

> change-id: `worktree-first-isolation`
> 路径建议: 增量，理由：改动仅涉及 references/ 下的 Markdown 文件 + 1 个 Python 脚本，不需要部署
> 复杂度: STANDARD

## 动机

flow-go 归档流程曾出现系统性漏洞：`.specs/` 下存在已完成但未归档的孤儿目录（feat-dev-optimize、kim-borrow-enhancement，已临时清理归档但根因未修复）。根因是 change 在主仓库中共享工作目录，导致：

1. 并行 change 的文件交叉污染（change B 的 commit 吸收了 change A 的工作）
2. STATE.md 索引表与实际 `.specs/` 目录脱节
3. 归档移动失败但 STATE.md 已清空

**根治方案**：每个 change 从创建 change-id 时就在独立 worktree 中工作，用 git 的物理隔离替代手动同步。

## 改动范围

### 改动 1: worktree 创建前移到 change-id 生成时

**当前**：worktree 在 2-任务阶段步骤 0 才创建（`references/stages/2-task.md`）
**改为**：worktree 在 0-需求阶段生成 change-id 后立即创建

- `SKILL.md` 第一步（读状态）：启动时用 `git worktree list` 替代 STATE.md 索引表作为活跃 change 真相源
- `SKILL.md` 第三步（意图路由）：新 change 在路由确定后、闸门检查前创建 worktree
- `references/stages/0-requirement.md`：步骤 3（生成 change-id）后新增 worktree 创建步骤
- `references/stages/2-task.md`：移除步骤 0 的 worktree 创建（已在 0-需求阶段完成）

### 改动 2: 根 STATE.md 简化 + SKILL.md 索引表逻辑清除

**当前**：根 STATE.md 已临时改为无索引表格式，但 SKILL.md 中仍有 7 处索引表相关逻辑（读索引表、解析活跃 change、旧格式检测等）未清理
**改为**：正式废除索引表，清理 SKILL.md 中所有索引表引用

- `STATE.md`：确认仅保留 Pipeline 待续 + 更新时间
- `SKILL.md`：清除索引表解析、旧格式检测、活跃数判断等逻辑，替换为 `git worktree list` 调用
- `references/stages/special-flows.md`：归档流程不再需要"从 STATE.md 索引表移除该 change 行"
- `references/artifacts/meta-artifacts.md`：更新 STATE.md 模板

### 改动 3: flow-go 启动路由重写

**当前**：读 STATE.md 索引表 → 解析活跃 change
**改为**：`git worktree list` → 过滤 `change/*` 分支 → 读各 worktree 的 `.specs/<id>/STATE.md`

- `SKILL.md` 第一步：重写活跃 change 发现逻辑
- 多 worktree 时列出选项让用户选择
- 单 worktree 时自动进入

### 改动 4: 归档流程拆分

**当前**：归档全部在当前工作目录完成
**改为**：per-change 清理在 worktree 内，全局文件更新在 main 仓库

- `references/stages/special-flows.md`：
  - 归档步骤 1-7（SUMMARY、LESSONS、PROGRESS 清理、目录移动）在 worktree 内执行
  - 归档步骤 8-9（ARCHIVE-INDEX、health-history.jsonl、traces.jsonl 追加）在 worktree commit 后、merge 回 main 时在 main 中执行
  - 新增 merge 回 main 后的全局文件追加步骤

### 改动 5: validate_state.py 重写

- 移除索引表校验逻辑
- 新增 `git worktree list` 校验（worktree 分支存在 = 活跃 change）
- per-change STATE.md 校验不变
- 向后兼容：归档目录中的旧格式 STATE.md 仍可读取

### 改动 6: 归档 commit 前完整性断言

- `references/stages/special-flows.md`：git commit 前增加断言——`.specs/<id>/` 目录不存在
- `references/common/archive-move.md`：已有硬闸门验证，无需修改

### 改动 7: commit message 强化 change-id 关联

- `references/stages/special-flows.md`：归档 commit 消息格式已含 change-id，增加非归档 commit 的规范——所有 commit 消息应含 change-id（如 `feat(flow-go)(<change-id>): ...`）

## 不做的事情

| 不做 | 原因 |
|------|------|
| gate_check.py 修改 | 仅读 per-change STATE.md，不受索引表变更影响 |
| health_scorer.py 逻辑修改 | 仅调整调用位置（从 worktree 内移到 main 中），核心逻辑不变 |
| evolution_signal.py 修改 | 仅读 per-change 文件，不受影响 |
| 全局文件同步自动化 | 当前阶段手动 merge 后执行全局追加，未来可独立 change 自动化 |

## AC（验收标准）

| # | AC | 优先级 | 验证方式 |
|---|-----|-------|---------|
| 1 | 新 change 启动时自动创建 worktree（`change/<id>` 分支），主仓库 STATE.md 无索引表 | P0 | 启动新 change → `git worktree list` 显示新 worktree + 主仓库 STATE.md 无活跃 Change 表 |
| 2 | `git worktree list` 替代 STATE.md 索引表作为活跃 change 真相源 | P0 | 删除 STATE.md 索引表 → flow-go 启动仍能正确发现活跃 change |
| 3 | 并行 change 在各自 worktree 中互不干扰 | P0 | 启动 change A + change B → 各自 worktree 独立 → A 的 commit 不含 B 的文件 |
| 4 | 归档流程正确处理 worktree：per-change 在 worktree 内，全局文件在 main 中 | P0 | 完整归档一个 change → worktree 清理 → main 中 ARCHIVE-INDEX/health-history/traces 已更新 |
| 5 | validate_state.py 支持新格式（无索引表）+ 向后兼容旧归档 | P1 | `pytest tests/` 全通过 |
| 6 | 归档 commit 前断言：.specs/<id>/ 不存在才允许 commit | P1 | 归档流程中 mv 失败 → 断言拦截 → commit 不执行 |
| 7 | 回归测试：现有归档 change 的 STATE.md 仍可读取 | P1 | 读取 `.specs/archive/` 下旧格式 STATE.md 无报错 |
| 8 | 回归测试：gate_check.py 功能不受影响 | P1 | `pytest tests/` 中 gate 相关测试全通过 |

## 验证假设

| # | 假设 | 证据级别 | 验证方式 | 验证阶段 | 推翻信号 |
|---|------|---------|---------|---------|---------|
| 1 | `git worktree list` 在所有支持环境（WSL2/macOS/Linux）行为一致 | B | 文档确认 + 实测 | 3-开发 | 某平台输出格式不一致 |
| 2 | 并行 worktree 的全局文件（health-history.jsonl 等）在 merge 时无冲突 | C | 3-开发阶段冒烟测试：创建两个并行 change 模拟归档 merge | 3-开发 | merge 时全局文件冲突 |
| 3 | worktree 创建在 0-需求阶段不会显著增加流程启动延迟 | C | 计时对比 | 3-开发 | 启动延迟 > 5 秒 |

## 终止条件

| # | 条件 | 触发阶段 | 触发后动作 |
|---|------|---------|-----------|
| 1 | `git worktree list` 在目标环境不可用或行为异常 | 3-开发 | 回退到索引表方案（改动 2 不做），仅保留 worktree 创建前移 |
| 2 | 全局文件 merge 冲突无法通过追加顺序解决 | 7-验收 | 全局文件改为仅在 main 中操作（改动 4 保留但简化） |

## 影响面

- REQUIREMENT: 否
- 架构: 是（改变 change 生命周期管理方式）
- AC: 是（新增 8 条验收标准）
- CONTEXT: 否
