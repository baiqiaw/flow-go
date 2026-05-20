# DEPLOY — skill-evolver-optimization

## 前置 4 问
- [x] change 都 merge 到主干了（已提交 commit 6d4ff87）
- [ ] 主干跟生产有 diff（本地工具，无生产环境）
- [ ] 必须立刻让用户看到（本地工具，用户自行更新）
- [ ] 有外部用户 / 生产环境（个人开发工具，无外部用户）

## 部署方案
- 平台：本地文件系统
- 方式：手动（git pull 即部署）
- 环境：local only

## 健康检查
| 检查项 | 结果 |
|--------|------|
| 所有 verify 命令通过 | ✅ 9/9 |
| gate_check.py CLI 3 模式可用 | ✅ |
| 新增模块可正常 import | ✅ 7/7 |
| 无新增外部依赖 | ✅ |

## 替代路径
本地工具，无需 CI/CD。用户通过 `git pull` 更新即可。变更已提交到 main 分支。

## 回滚方案
```bash
git revert 6d4ff87
```
gate_check.py 原函数签名保持向后兼容，revert 不会破坏现有调用方。

## 监控
- 告警规则：不适用（本地工具）
- 看板链接：不适用
