# CHANGE — skills-borrow

## Why（为什么做）
借鉴 mattpocock/skills（9.4万Star）的四阶段反 Vibe Coding 方法论中的 8 项优秀经验，补齐 flow-go 在项目记忆、结构化调试、任务分类、接口设计纪律方面的短板。同时修复此前更新中闸门脚本的格式不一致回归问题。

## What（做什么）
1. 引入 ADR（架构决策记录）机制，持久化跨 change 的架构决策
2. 引入项目词典（CONTEXT.md）机制，在需求阶段自动建立和维护领域词汇
3. 为任务增加 AFK/HITL 模式标记，提升并行效率
4. 在开发阶段增加结构化调试子流程（6阶段 diagnose）
5. 在任务拆分中强调垂直切片原则，替换隐含的水平拆分倾向
6. 在设计阶段增加深模块原则和 Seams 纪律指导
7. 为 HEAVY 复杂度增加可选原型子阶段
8. 修复闸门脚本（gate_check.py / validate_state.py）的格式不一致问题

## 影响面
- 涉及模块：stages（0,1,2,3）、artifacts（spec, task）、scripts（gate_check, validate_state）、SKILL.md、新增模板文件
- 数据库变更：否
- API 变更：否
- 依赖变更：否
- CONTEXT 需更新：是（新增 ADR 和 CONTEXT 机制本身需要记录）

## 范围排除（这次不做）
- 不实现 Caveman 模式（中文语境不适合极简表达）
- 不实现独立的 Issue 状态机（flow-go 已有更完善的闸门体系）
- 不实现 CONTEXT-MAP.md 多上下文（flow-go 面向单项目场景）
- 不改造现有归档体系结构（仅扩展内容）
- 不引入新的外部依赖

## 验收线
8 项借鉴经验全部在对应阶段/模板中落地，闸门脚本 gate_check.py 和 validate_state.py 输出格式统一且通过全部验证。

## 路径建议
完整路径，理由：涉及 8 个独立改动点，横跨 4 个阶段和多个工件模板，需要设计→任务→开发→测试全流程保障质量。
