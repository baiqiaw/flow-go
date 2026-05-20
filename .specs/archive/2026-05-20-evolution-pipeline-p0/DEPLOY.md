# DEPLOY — evolution-pipeline-p0

## 前置 4 问
- [x] change 都 merge 到主干了
- [ ] 主干跟生产有 diff
- [ ] 必须立刻让用户看到
- [ ] 有外部用户 / 生产环境

## 替代路径
本项目为本地 CLI 工具集（`references/scripts/`），无生产环境、无外部用户、无 CI/CD 流水线。所有脚本改动已在 main 分支，用户可直接通过 `python3 references/scripts/<script>.py` 调用。

## 部署方案
- 平台：本地文件系统
- 方式：已就位（git commit 在 main）
- 环境：本地开发环境

## 健康检查
| 检查项 | 结果 |
|--------|------|
| evolution_signal.py --specs-dir 可调用 | ✅ |
| gate_check.py --mode quality-gate 可调用 | ✅ |
| health_scorer.py --format json 可调用 | ✅ |
| 旧调用方式向后兼容 | ✅ |

## 回滚方案
`git revert` 回退本次 change 的 6 个提交即可。

## 监控
无外部监控需求。脚本运行时 stderr 输出警告信息，符合可观测要求。
