# REQUIREMENT — CH-20260522-001

## 用户故事
作为 flow-go 维护者，我想借鉴 Karpathy Skills 的简洁落地方式优化 flow-go 的可操作性，以便规则执行更一致、新用户上手门槛更低。

## 验收准则（BDD）

### AC-1 阶段自检锚点
**Given**: flow-go 的 8 个阶段各有反模式和行为规则
**When**: 开发员/测试员/审查员进入任一阶段
**Then**: 角色声明中包含一句可秒记的自检锚点口诀（≤15字），且该口诀出现在精炼环/闸门检查的对应位置

### AC-2 权衡声明
**Given**: SKILL.md 是 flow-go 的入口文件
**When**: 用户首次阅读 SKILL.md
**Then**: 开头区域（前 20 行内）有明确的权衡声明，说明 flow-go 偏向严谨而非速度，以及何时可简化

### AC-3 反模式实例对照
**Given**: flow-go 已有 anti-patterns.md（抽象表格）
**When**: 开发员需要理解某条反模式的具体表现
**Then**: references/anti-pattern-examples.md 提供至少 6 组 ❌/✅ 代码对照，覆盖 scope creep、over-engineering、drive-by refactor、skip-clarification、fake-verify、weaken-failing 高频反模式

### AC-4 精炼环直觉检验
**Given**: 3-开发阶段有精炼环（STANDARD/HEAVY）
**When**: 精炼环执行到反模式清零步骤
**Then**: 包含一条「资深工程师直觉」检验："资深工程师看了会说'太复杂了'吗？→ 是则简化"

### AC-5 归档成功指标
**Given**: 归档流程在 special-flows.md 中定义
**When**: 归档完成时
**Then**: 输出 3 条简明成功指标（Diff 无关改动减少？/ 假设错误返工减少？/ 澄清问题在实现前提出？），用于用户快速判断 flow-go 是否生效

## 非功能需求
- 性能：新增文件不增加常驻 token（按需 grep 加载）
- 兼容：不破坏现有 flow-go 流程和状态管理

## Out of Scope（范围排除）
- LITE 轻量计划模板改造
- 最小启动配置/渐进式采纳设计
- 核心编排逻辑修改

## Principles（设计约束原则）
- 新增内容遵循「按需加载」原则（grep 加载，不常驻）
- 口诀锚点 ≤ 15 字，可秒记
- ❌/✅ 实例用伪代码，不依赖具体语言

## Key Decisions（关键决策记录）
| 决策 | 理由 | 影响 |
|------|------|------|
| 只实施 P0+P1 共 5 项 | P2/P3 需改路由逻辑，风险和复杂度更高 | 本次范围明确，后续可追加 |
| 实例对照独立文件而非内嵌 anti-patterns.md | 保持 anti-patterns.md 简洁，按需加载 | 新增 1 个 reference 文件 |
| 口诀嵌入角色声明和闸门 | 最高频触达点，确保每次进入阶段都可见 | 需改 SKILL.md 角色声明模板 |

## 术语表
| 术语 | 含义 |
|------|------|
| 自检锚点 | 一句话口诀，帮助角色快速记忆核心行为约束 |
| 精炼环 | 3-开发阶段 task 完成后的代码质量自检流程 |
| ❌/✅ 对照 | 错误做法 vs 正确做法的代码实例对比 |
| 权衡声明 | upfront 说明工具的偏好和代价 |
