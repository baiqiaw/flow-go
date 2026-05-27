# DEPLOY — token-optimize-p0-p2

**运维角色**：运维
**部署时间**：2026-05-27

## 前置 4 问

| 问题 | 回答 |
|------|------|
| change 都 merge 到主干了？ | 否（当前在 worktree 分支 worktree-token-optimize-p0-p2） |
| 主干跟生产环境有 diff？ | N/A（内部工具，无生产环境） |
| 必须立刻让用户看到？ | 是 |
| 有外部用户 / 生产环境？ | 否（纯内部 AI 流程编排工具） |

## 部署方式

**类型**：内部工具 — 合并到 main 分支即生效。

**步骤**：
1. 确认所有阶段工件齐全（CHANGE/REQUIREMENT/DESIGN/TASK/TEST/REVIEW/SUMMARY×10）
2. 确认所有审查通过（矩阵 A/B/C 全 PASS，0 问题）
3. 合并 worktree 分支到 main
4. 清理 worktree

## 构建/测试

- 无构建步骤（纯 Markdown + Node.js + Python 脚本）
- 回归测试：27/27 pytest 通过

## 健康检查

| 检查项 | 状态 |
|--------|------|
| pytest 回归测试 | 27/27 PASS |
| Hook 功能验证 | 3/3 场景 PASS |
| 交叉评审 | 矩阵 A/B/C 全 PASS |
| 密钥扫描 | 无泄露 |

## 回滚方案

```
git checkout main
git reset --hard a591aec
```

回滚后恢复到 P0-P2 优化前的状态。

## 监控

N/A（内部工具，无运行时监控需求）
