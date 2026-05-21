# DEPLOY — state-parallel

## 前置 4 问
- [x] change 都 merge 到主干了 — 已在 main 分支，3 次 commit（开发+测试+审查）
- [ ] 主干跟生产有 diff — 不适用（无生产环境）
- [ ] 必须立刻让用户看到 — 否（本地工具框架更新）
- [ ] 有外部用户 / 生产环境 — 否

## 替代路径
前置 4 问中 3 项 ❌，走替代路径：
- 本项目为文档/工具框架（SKILL.md + references/），非运行时服务
- 变更已在 main 分支 commit，本地立即可用
- 无需 CI/CD、staging、prod 部署流程
- 用户 `git pull` 即可获得更新

## 部署方案
- 平台：Git 仓库（本地）
- 方式：直接 commit 到 main（已完成）
- 环境：本地开发环境，无多环境需求

## 健康检查
| 检查项 | 结果 |
|--------|------|
| validate_state.py 正常运行 | ✅ passed: true |
| gate_check.py 正常运行 | ✅ passed: true |
| SKILL.md 格式完整 | ✅ 361 行，无语法错误 |
| stages/0-7 格式完整 | ✅ 9 个文件，per-change 引用已覆盖 |

## 回滚方案
- `git revert HEAD~3..HEAD` 可回退全部 3 个 commit
- 无数据迁移，回退无风险

## 监控
- 无需监控配置（非运行时服务）
- 后续会话使用 flow-go 时自动验证新格式
