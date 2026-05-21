# REQUIREMENT — worktree-isolation

## 需求描述
为 flow-go 流程编排增加 git worktree 隔离机制。每个 change 在设计评审通过后、进入任务拆分阶段前，自动创建以 `change/<id>` 为分支名的 git worktree，所有后续开发工作在该 worktree 中进行。归档时自动合并回 main 并清理 worktree；废弃时直接清理 worktree。

## 目标用户
- 使用 flow-go 的开发者（手动触发 go 指令）
- AI agent（执行 flow-go 流程编排）

## 验收标准（BDD）

### AC-1: Worktree 创建
```gherkin
Given 一个 change 完成了 1-设计阶段且设计评审 PASS
When 进入 2-任务阶段前
Then 自动创建名为 "change/<id>" 分支的 git worktree
And 自动切换到该 worktree 继续后续阶段工作
And STATE.md 记录 worktree 路径信息
```

### AC-2: 代码隔离
```gherkin
Given 一个 change 有活跃的 worktree
When 在 3-开发阶段编写代码并提交
Then 所有代码改动在 worktree 中提交
And 主仓库 working tree 无该 change 的代码改动
```

### AC-3: 归档合并
```gherkin
Given 一个 change 完成全部阶段进入归档流程
When 执行归档步骤
Then 自动将 worktree 分支合并到 main 分支
And 合并冲突时停下来提示用户手动解决
```

### AC-4: Worktree 清理
```gherkin
Given 归档合并已完成
Then 自动删除 worktree 目录
And 自动删除对应的 "change/<id>" 分支
And 切换回主仓库工作目录
```

### AC-5: 废弃清理
```gherkin
Given 一个有活跃 worktree 的 change 被废弃
When 执行废弃流程
Then 删除 worktree 目录和对应分支（不合并）
And 切换回主仓库工作目录
```

### AC-6: 仓库干净
```gherkin
Given 归档或废弃流程完成
When 检查仓库状态
Then git status 显示 clean
And git worktree list 仅显示主仓库
And 无残留的 change/<id> 分支
```

### AC-7: 回溯恢复
```gherkin
Given 一个被中断的 change 有活跃 worktree
When 用户请求恢复（回溯/继续）
Then 自动识别该 change 有 worktree
And 切换到对应 worktree 继续工作
```

## 范围排除
- 不改变角色分工和闸门检查逻辑
- 不支持跨仓库 worktree（仅限单仓库内）
- 不实现 worktree 内部的依赖隔离
- 不实现 worktree 权限管理

## 影响面判定
- 涉及流程配置：影响 SKILL.md 主路由、special-flows.md（归档/废弃/中断）、3-develop.md
- 涉及状态管理：STATE.md 需新增 worktree 路径字段
- 不涉及架构变更、数据库、API
