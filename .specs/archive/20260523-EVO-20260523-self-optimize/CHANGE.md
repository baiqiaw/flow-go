# CHANGE — 进化系统自优化

## 变更描述
优化 flow-go 自我进化系统，使其在其他项目中使用时也能正常触发。当前进化路径（CAPTURE/FIX/BITTER PILL/SUGGEST）在新项目中从不触发，核心原因是触发链路过长、依赖手动步骤、缺少闭环反馈。

## 变更类型
- [x] 重构/优化
- [ ] 新功能
- [ ] Bug 修复
- [ ] 文档

## 影响范围
- `SKILL.md` — 进化触发逻辑、归档自检清单
- `references/stages/special-flows.md` — 归档流程增加健康评分自动计算和进化检查项
- `references/scripts/evolution_signal.py` — 信号检测增加模糊匹配
- `references/scripts/_path_utils.py` — 增加 skill 目录自动发现
- `references/stages/1-design.md` — 注入历史策略（CAPTURE 闭环）
- `references/stages/3-develop.md` — 注入历史策略（CAPTURE 闭环）

## 涉及文件数
约 7 个文件
