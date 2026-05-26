# REQUIREMENT — worktree-first-isolation

## 用户故事

**作为 flow-go 的开发者**，我希望每个 change 从创建时就在独立 worktree 中工作，这样并行 change 不会交叉污染，归档不再产生孤儿目录。

**当前痛点**：
- `.specs/` 下出现已完成但未归档的孤儿目录，主仓库 STATE.md 却显示"无活跃 Change"
- 并行 change 的工作互相吸收——change B 的 commit 包含了 change A 的改动
- 归档流程手动维护 STATE.md 索引表，容易与实际 `.specs/` 目录脱节

## 术语表

| 术语 | 定义 | 避免别名 |
|------|------|---------|
| worktree-first | 每个 change 从创建 change-id 时就在独立 git worktree 中工作的模式 | 工作树优先 |
| 真相源 | 活跃 change 的权威数据来源，由 `git worktree list` 替代 STATE.md 索引表 | source of truth |
| 全局文件 | 跨 change 共享的追加写入文件（ARCHIVE-INDEX.md、health-history.jsonl、traces.jsonl） | global files |
| per-change 文件 | 单个 change 私有的工件文件（STATE.md、REQUIREMENT.md 等） | change 级文件 |

## BDD 验收标准

### AC-1: worktree 自动创建

```gherkin
Given 用户启动新 change（0-需求阶段）
When change-id 生成完成
Then 自动创建 git worktree（分支 change/<id>，路径 .claude/worktrees/<id>）
And per-change STATE.md 写入 worktree_path 字段
And 主仓库 STATE.md 无索引表更新
```

### AC-2: git worktree list 作为真相源

```gherkin
Given flow-go 启动
When 读取活跃 change 列表
Then 使用 git worktree list 过滤 change/* 分支
And 不依赖 STATE.md 索引表
And 能正确发现所有活跃 worktree
```

### AC-3: 并行 change 隔离

```gherkin
Given 存在活跃 change A（worktree A）
When 用户启动新 change B（worktree B）
Then change B 的文件修改仅在 worktree B 中
And change A 的文件不受影响
And 两个 worktree 可独立 commit
```

### AC-4: 归档流程拆分

```gherkin
Given change 在 worktree 中完成所有阶段
When 执行归档流程
Then per-change 清理（PROGRESS 删除、目录移动到 archive/）在 worktree 内完成
And worktree commit 后 merge 回 main
And 全局文件（ARCHIVE-INDEX、health-history、traces）在 main 中追加
And worktree 最终被清理
```

### AC-5: validate_state.py 新格式支持

```gherkin
Given 根 STATE.md 无索引表（仅 Pipeline + 更新时间）
When 执行 python3 references/scripts/validate_state.py
Then 校验通过（不报索引表缺失错误）
And per-change STATE.md 校验仍正常工作
And 旧归档目录中的 STATE.md 仍可读取
```

### AC-6: 归档 commit 前完整性断言

```gherkin
Given 归档流程准备执行 git commit
When 检查 .specs/<id>/ 目录
Then 如果目录仍存在 → 中断提交并报错
And 如果目录不存在（已移到 archive/）→ 允许提交
```

### AC-7: 旧归档向后兼容

```gherkin
Given .specs/archive/ 下存在旧格式 STATE.md（含索引表）
When 读取这些文件
Then 不报错，内容正确解析
```

### AC-8: gate_check.py 不受影响

```gherkin
Given gate_check.py 从 .specs/<id>/STATE.md 读取阶段信息
When 执行闸门检查
Then 功能与改动前一致
And 现有测试全部通过
```

## 关键决策

| 决策 | 选项 | 选择 | 理由 |
|------|------|------|------|
| 活跃 change 真相源 | STATE.md 索引表 / git worktree list | git worktree list | 消除手动同步，git 保证一致性 |
| worktree 创建时机 | 2-任务 / 0-需求（change-id 生成后） | 0-需求 | 从源头隔离，防止早期阶段交叉污染 |
| 全局文件更新位置 | worktree 内 / merge 后在 main 中 | merge 后在 main 中 | 避免并行 worktree 的全局文件 merge 冲突 |
| 根 STATE.md 格式 | 保留索引表 / 废除索引表 | 废除索引表 | 既然真相源是 git，保留索引表只会增加同步负担 |

## 影响文件清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `SKILL.md` | 修改 | 第一步重写（worktree list 替代索引表）、第三步新增 worktree 创建、第七步状态更新简化 |
| `references/stages/0-requirement.md` | 修改 | 步骤 3 后新增 worktree 创建步骤 |
| `references/stages/2-task.md` | 修改 | 移除步骤 0 的 worktree 创建 |
| `references/stages/special-flows.md` | 修改 | 归档流程拆分（per-change 在 worktree / 全局在 main）、新增 commit 前断言 |
| `references/artifacts/meta-artifacts.md` | 修改 | STATE.md 模板更新 |
| `references/scripts/validate_state.py` | 重写 | 移除索引表逻辑，新增 worktree list 校验 |
| `references/common/archive-move.md` | 不变 | 已有硬闸门验证 |
| `references/scripts/gate_check.py` | 不变 | 仅读 per-change STATE.md |
| `references/scripts/health_scorer.py` | 不变 | 仅调整调用位置（special-flows.md 控制） |

## 范围排除

| 不做 | 原因 |
|------|------|
| 全局文件 merge 自动化 | 当前阶段手动 merge 后执行全局追加，未来可独立 change |
| worktree 资源管理（过期清理等） | 独立关注点，不与本 change 混合 |
| 多 worktree 并行执行框架 | 本 change 只解决隔离问题，并行调度是独立 feature |
