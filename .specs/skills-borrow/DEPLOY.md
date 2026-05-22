# DEPLOY — skills-borrow

## 部署评估

### 前置 4 问

| 问题 | 回答 | 说明 |
|------|------|------|
| change 都 merge 到主干了？ | ✅ | 代码在 main 分支，commit 876d4d9, adafe06, 80dece8 |
| 主干跟生产环境有 diff？ | ❌ | 本地 skill 项目，无生产环境 |
| 必须立刻让用户看到？ | ❌ | 变更为 skill 参考文件，无用户可见 UI |
| 有外部用户 / 生产环境？ | ❌ | 仅开发者本地使用 |

### 决策：替代路径

前置 4 问中 3 个 ❌，按 6-deploy.md 自检清单第 3 条走替代路径：**本地工具/技能变更不需要走部署流程**。

变更内容为 flow-go skill 的参考文件（阶段文件、工件模板、闸门脚本），已通过交叉评审和测试验证，直接在 main 分支可用。

### 健康检查

| 检查项 | 结果 |
|--------|------|
| 闸门脚本可执行 | ✅ gate_check.py / validate_state.py 正常运行 |
| 阶段文件完整 | ✅ 0-requirement / 1-design / 2-task / 3-develop 内容完整 |
| 新增文件存在 | ✅ memory-artifacts.md 存在且格式正确 |
| SKILL.md 一致性 | ✅ CONTEXT/ADR/AFK/原型路由均已集成 |

### 回滚方案

git revert 对应 commit 即可回滚。

### 监控配置

不适用（无生产环境）。
