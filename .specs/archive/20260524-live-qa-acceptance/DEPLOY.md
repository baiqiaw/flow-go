# DEPLOY — live-qa-acceptance

## 前置 4 问
- [x] change 都 merge 到主干了 — commit e211513 在 main 分支
- [ ] 主干跟生产环境有 diff — ❌ 本地流程框架，无生产环境
- [ ] 必须立刻让用户看到 — ❌ 本地 skill 文件，下次会话自动生效
- [ ] 有外部用户 / 生产环境 — ❌ 仅本机开发者使用

## 替代路径
flow-go 是本地 AI 开发流程框架（纯 markdown 文件），变更位于 `~/.claude/skills/flow-go/references/` 目录。无需 CI/CD、staging/prod 部署流程。commit 已在 main 分支，变更即时可用。

变更文件：
- references/stages/7-acceptance.md（+67/-16 行）
- references/artifacts/deploy-artifacts.md（+23 行）
- references/gate-rules.md（+6/-2 行）

## 部署方案
- 平台：N/A（本地文件系统）
- 方式：git commit 已完成，无需额外部署动作
- 环境：local（无 dev/staging/prod 区分）

## 健康检查
| 检查项 | 结果 |
|--------|------|
| 回归测试 26/26 | ✅ |
| 闸门脚本 gate_check.py | ✅ passed |
| 文件完整性（3 文件 diff 对齐 TASK.md） | ✅ |

## 替代路径（如有 ❌）
本地工具，无需部署。变更已通过完整开发→测试→审查流程验证。

## 回滚方案
`git revert e211513` 即可回退所有变更。

## 监控
- 告警规则：N/A
- 看板链接：N/A

## 部署时间
2026-05-24（替代路径：无需部署动作）
