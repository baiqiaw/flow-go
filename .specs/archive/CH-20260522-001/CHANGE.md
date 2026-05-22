# CHANGE — CH-20260522-001

## Why（为什么做）
分析 vercel-labs/agent-skills 的 web-design-guidelines skill 后发现 5 项可借鉴的架构经验。当前 SKILL.md 内联了闸门规则、角色约束等静态知识（约 40 行区间），导致主文件臃肿、规则难以独立迭代、无法被脚本自动检查。需要将这些知识外置为原子化规则文件，并将"原子化+结构化输出"经验注入进化机制。

## What（做什么）
1. 将 SKILL.md 中闸门检查表、角色约束表外置到 `references/gate-rules.md`（反模式继续使用已有 `references/anti-patterns.md`，新增原子化 id 格式与之对齐）
2. anti-patterns.md 原子化增强：为现有反模式条目添加 `id` 字段（格式 `阶段-序号-关键词`）
3. 闸门检查输出结构化格式（`STAGE-N: artifact ✅ / artifact ❌`）
4. gate_check.py 支持 `--categories` 参数按类别执行检查
5. 将借鉴经验（原子化规则、结构化输出、关注点分离、单一职责、可组合规则）注入进化分析机制，使后续优化自动遵循这些原则

## 影响面
- 涉及模块：SKILL.md、references/、references/scripts/gate_check.py、references/scripts/evolution_reflect.py
- 数据库变更：否
- API 变更：是（gate_check.py 新增 --categories 参数）
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- 不改变阶段流程和路由逻辑
- 不修改 references/stages/ 下的阶段定义文件
- 不修改 gate_check.py、evolution_reflect.py 以外的脚本
- 不改变 STATE.md 状态管理机制

## 验收线
SKILL.md 主文件闸门/角色约束外置完成 + gate-rules.md 创建 + anti-patterns.md 添加 id 字段 + gate_check.py 支持 --categories + 进化机制包含 5 项架构原则

## 路径建议
增量路径，理由：改动集中在 SKILL.md + references/ 目录，不涉及核心流程逻辑，风险可控。SKILL.md 引用替换为文件加载即可。
