# DEPLOY — change-pipeline

## 部署类型
本地 skill 文件提交（非应用部署）

## 变更范围
| 文件 | 变更 |
|------|------|
| SKILL.md | 路由表+步骤1+步骤7 新增 Pipeline 逻辑 |
| references/artifacts/meta-artifacts.md | STATE.md schema + PIPELINE.md 模板 + .lock 模板 |
| references/stages/0-requirement.md | 步骤2 拆分联动增强 |
| references/stages/3-develop.md | 锁机制（检查+创建+释放） |
| references/stages/special-flows.md | 归档衔接+中断流程+并行启动+回溯增强 |
| STATE.md | 格式迁移为 Markdown 标题+列表（7 字段） |

## 提交信息
`feat(change-pipeline): 新增 PIPELINE.md 排队+中断恢复+并行安全机制`

## 提交 SHA
23a0b48

## 健康检查
- git status: clean ✓
- 22 文件变更，+1458/-32 行 ✓

## 回滚方案
`git revert 23a0b48`

## 监控/告警
不适用（skill 文件无运行时监控）

## 部署时间
2026-05-20
