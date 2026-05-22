# REQUIREMENT — CH-20260522-001

## 用户故事
作为 flow-go skill 维护者，我想将内联规则外置为原子化规则文件并注入架构原则到进化机制，以便 skill 主文件保持简洁、规则可独立迭代、后续优化自动遵循最佳实践。

## 验收准则（BDD）

### AC-1 规则外置到独立文件
**Given**: SKILL.md 中闸门检查表、角色约束表为内联内容（反模式已有 `references/anti-patterns.md`）
**When**: 执行外置重构
**Then**: 闸门检查表和角色约束表移至 `references/gate-rules.md`，SKILL.md 通过 grep 加载引用，SKILL.md 主文件减少 ≥30 行

### AC-2 反模式清单原子化增强
**Given**: `references/anti-patterns.md` 已有结构化反模式（Anti-Pattern/Why It Fails/Better Approach 三列）
**When**: 原子化增强完成
**Then**: 每条反模式添加唯一 `id` 字段（格式 `阶段-序号-关键词`），可被脚本逐条 grep 检查

### AC-3 闸门检查结构化输出
**Given**: 闸门检查结果为自然语言描述
**When**: 调用 gate_check.py 或手动检查
**Then**: 输出格式为 `STAGE-N: artifact ✅ / artifact ❌ / artifact ⚠️`，每行一个工件

### AC-4 gate_check.py 按类别检查
**Given**: gate_check.py 当前全量检查所有闸门
**When**: 传入 `--categories security,scope` 参数
**Then**: 仅执行指定类别的检查，类别包括：gate（闸门前置）、antipattern（反模式）、role（角色约束）、safety（安全场景）

### AC-5 架构原则注入进化机制
**Given**: 进化分析机制（SUGGEST/BITTER PILL）当前无架构原则检查维度
**When**: 归档后触发进化分析
**Then**: 进化机制包含 5 项架构原则（原子化规则、结构化输出、关注点分离、单一职责、可组合规则），SUGGEST 路径自动检测违反原则的规则并生成改进建议

## 非功能需求
- 性能：gate-rules.md 按需 grep 加载，不增加冷启动负担
- 安全：外置规则不改变闸门严格程度，HARD-GATE 语义不变
- 兼容：gate_check.py 新增 `--categories` 为可选参数，不传时行为与现有一致

## Out of Scope（范围排除）
- 不改变 8 阶段流程定义
- 不修改阶段文件（stages/*.md）
- 不修改 gate_check.py、evolution_reflect.py 以外的脚本
- 不改变 STATE.md 状态管理
- 不引入远程 URL 动态加载（保持离线友好）

## Principles（设计约束原则）
- 外置规则必须保持 HARD-GATE 语义不变
- SKILL.md 引用替换为 grep 加载模式（与现有 reference 加载方式一致，按需 grep 不整读）
- 原子化规则每条可独立引用，无隐式依赖
- 进化原则检测为建议性质（SUGGEST），不阻塞归档

## Key Decisions（关键决策记录）
| 决策 | 理由 | 影响 |
|------|------|------|
| 不采用远程 URL 动态加载 | flow-go 离线友好是核心需求 | 保持本地文件加载模式 |
| 进化原则注入 SUGGEST 路径 | 不阻塞归档流程，仅生成建议 | 需扩展 evolution_reflect.py |
| 反模式 id 格式：`阶段-序号-关键词` | 便于 grep 定位和脚本引用 | gate-rules.md 中统一格式 |

## 术语表
| 术语 | 含义 |
|------|------|
| 原子化规则 | 每条规则可独立执行、独立验证的最小检查单元 |
| 结构化输出 | `key: value` 格式的机器可读输出，而非自然语言描述 |
| 可组合规则 | 规则可按类别组合执行，支持选择性检查 |
| 关注点分离 | 编排逻辑（SKILL.md）与领域知识（references/）独立存放 |
| 进化原则 | 注入到进化分析中的架构最佳实践，用于指导后续优化 |
