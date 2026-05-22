# CHANGE — CH-20260522-001

## Why（为什么做）
flow-go 的机制深度远超 Karpathy Skills（70 行 CLAUDE.md），但缺乏 Karpathy 的 3 个关键优势：简洁可记忆的自检锚点、❌/✅ 实例对照、前置权衡声明。导致规则虽全面但执行时容易被忽略或记忆模糊。

## What（做什么）
借鉴 Karpathy Skills 的 4 条行为准则和 EXAMPLES.md 的落地方式，对 flow-go 的 references/ 体系进行 5 项优化：
1. 为每阶段增加一句话自检锚点口诀
2. 在 SKILL.md 开头增加权衡声明
3. 新增 anti-pattern-examples.md（❌/✅ 代码对照）
4. 精炼环增加「资深工程师直觉」检验项
5. 归档/验收增加 3 条简明成功指标

## 影响面
- 涉及模块：SKILL.md、references/anti-patterns.md、references/gate-rules.md、stages/3-develop.md、stages/7-acceptance.md、stages/special-flows.md
- 数据库变更：否
- API 变更：否
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- 不改动 LITE 轻量计划模板（P2，需改路由逻辑）
- 不做最小启动配置（P3，需改路由逻辑）
- 不改变 flow-go 核心流程编排逻辑
- 不改动状态管理机制

## 验收线
5 项优化全部落地，diff 可追溯，无新增 TBD/占位符。

## 路径建议
增量，理由：在现有 references/ 文件基础上追加/修改，不改变核心编排逻辑。
