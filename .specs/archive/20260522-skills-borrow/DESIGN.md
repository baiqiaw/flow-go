# DESIGN — skills-borrow

## 0. 技术栈选定
| 候选 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| 沿用现有（Python + Markdown） | 零依赖、风格一致、维护者熟悉 | — | ✅ |
最终选择：沿用现有技术栈，理由：8 项改动全部是对 flow-go 自身流程文件的增量修改，无外部依赖需求。

## 1. 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        SKILL.md（主调度）                         │
│  新增：CONTEXT.md 读取 → 术语注入 → ADR 检查路由                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ 0-需求    │    │ 1-设计    │    │ 2-任务    │    │ 3-开发    │  │
│  │          │    │          │    │          │    │          │  │
│  │ [NEW]    │    │ [NEW]    │    │ [NEW]    │    │ [NEW]    │  │
│  │ CONTEXT  │    │ ADR 机制  │    │ AFK/HITL │    │ 结构化   │  │
│  │ 自动维护  │    │ 深模块    │    │ 垂直切片  │    │ 调试流程  │  │
│  │ 术语检测  │    │ 原型子阶段│    │ 指导     │    │          │  │
│  └──────────┘    └──────────┘    └──────────┘    └──────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   持久化层                                │   │
│  │  .specs/CONTEXT.md  ← 项目词典（跨 change 持久）           │   │
│  │  .specs/adr/        ← ADR 目录（跨 change 持久）           │   │
│  │  .specs/<id>/        ← change 级工件（不变）               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   脚本层                                  │   │
│  │  gate_check.py      ← [FIX] 格式统一 + ADR/CONTEXT 检查   │   │
│  │  validate_state.py  ← [FIX] 格式统一                      │   │
│  │  gate_artifacts.py  ← [FIX] 工件清单与闸门表对齐            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 2. 数据流

### 2.1 CONTEXT.md 数据流
```
用户输入需求描述
    ↓
0-需求阶段：提取术语 → 写入 .specs/CONTEXT.md
    ↓
1-设计阶段：读取 CONTEXT.md → 用规范术语写 DESIGN.md → 术语冲突时提醒
    ↓
2-任务阶段：读取 CONTEXT.md → 任务描述使用规范术语
    ↓
3-开发阶段：读取 CONTEXT.md → 代码变量名/注释使用规范术语
    ↓
归档：CONTEXT.md 保留（跨 change 持久），不清除
```

### 2.2 ADR 数据流
```
1-设计阶段：讨论架构决策
    ↓
判断 ADR 条件（难以逆转 + 无上下文会困惑 + 有真实取舍）
    ↓ 满足
创建 .specs/adr/NNNN-<slug>.md（背景/选项/决策/理由）
    ↓
后续 change 进入设计阶段 → 自动扫描 .specs/adr/ → 避免重复建议已否决方案
    ↓
归档：ADR 保留（跨 change 持久），跟随项目生命周期
```

### 2.3 AFK/HITL 标记流
```
2-任务阶段：每个 <task> 标签增加 mode 属性
    ↓
TASK.md 中 mode="afk|hitl|colab"
    ↓
并行模式（parallel）→ 优先将 AFK 任务分配给独立 agent
```

## 3. 改动清单

### 3.1 新增文件

| 文件 | 用途 |
|------|------|
| `references/artifacts/memory-artifacts.md` | ADR 格式模板 + CONTEXT 格式模板 |

### 3.2 修改文件

| 文件 | 改动内容 |
|------|---------|
| `references/stages/0-requirement.md` | 步骤 4 增加：术语表写入 `.specs/CONTEXT.md`。步骤 6 增加：影响面判定增加"CONTEXT 需更新"的自动检查 |
| `references/stages/1-design.md` | 步骤 4 扩展：ADR 条件过滤（三条件全满足才创建）。步骤 4.1 新增：ADR 文件写入 `.specs/adr/`。步骤 4.2 新增：自动扫描已有 ADR 避免重复。步骤 6.1 新增：深模块原则指导。步骤 6.2 新增：Seams 纪律检查。步骤 X 新增：HEAVY 复杂度可选原型子阶段。上下文需求清单新增 CONTEXT.md 行 |
| `references/stages/2-task.md` | 步骤 3 增加：垂直切片原则（禁止水平切片）。`<task>` 标签新增 `mode` 属性。步骤 3.1 新增：AFK/HITL 标记指导 |
| `references/stages/3-develop.md` | 步骤 3.1 新增：结构化调试子流程（6 Phase）。步骤 3.2 新增：调试日志 `[DEBUG-xxxx]` 标记纪律 |
| `references/artifacts/spec-artifacts.md` | REQUIREMENT.md 模板无变动（已有术语表）。新增 ADR 模板引用（指向 memory-artifacts.md）。新增 CONTEXT 模板引用 |
| `references/artifacts/task-artifacts.md` | `<task>` 标签新增 `mode="afk\|hitl\|colab"` 属性定义。自检清单新增：mode 字段已填写 |
| `references/scripts/gate_check.py` | [FIX] 参数大小写标准化（接受 HEAVY/heavy）。新增 --stage 1 时检查 ADR 目录（HEAVY 模式）。新增 --stage 0 时检查 CONTEXT.md |
| `references/scripts/validate_state.py` | [FIX] 输出格式统一（✅/❌ 标记、缩进、字段名） |
| SKILL.md | 第一步读状态：增加读取 .specs/CONTEXT.md。第三步路由：原型子阶段路由。第四步闸门：增加 ADR/CONTEXT 检查行 |

## 4. ADR

### ADR-001 ADR 与 CONTEXT 的存储位置
- 背景：需要确定跨 change 持久化文件的存放位置
- 选项：A) `.specs/` 下 / B) 项目根目录 / C) `docs/` 下
- 决策：A) `.specs/` 下
- 理由：flow-go 以 `.specs/` 为中心管理所有规格文件，CONTEXT 和 ADR 属于流程内部概念。项目根目录留给最终用户的文件，`docs/` 留给用户文档。归档时这些文件自动保留。

### ADR-002 AFK/HITL 作为 TASK 属性而非独立工件
- 背景：需要为任务增加执行模式标记
- 选项：A) TASK 模板 `<task>` 标签新增 mode 属性 / B) 独立的 ASSIGNMENT.md 文件
- 决策：A) 新增 mode 属性
- 理由：最小化改动，复用现有模板结构，避免新增工件文件增加认知负担。

### ADR-003 调试流程嵌入 develop.md 而非独立文件
- 背景：结构化调试流程有 6 个 Phase，内容较多
- 选项：A) 嵌入 develop.md 作为子章节 / B) 独立 references/stages/3-diagnose.md
- 决策：A) 嵌入 develop.md
- 理由：调试是开发的子活动，保持阶段文件的完整性。开发员进入调试时不需要跳转到另一个文件。独立文件会增加 SKILL.md 的加载映射复杂度。

### ADR-004 闸门脚本大小写标准化策略
- 背景：gate_check.py --complexity 只接受小写，但 SKILL.md 和用户习惯使用大写
- 选项：A) 脚本内部统一转小写 / B) choices 列表同时包含大小写
- 决策：A) 脚本内部统一转小写（argparse parse 后 `.lower()`）
- 理由：保持用户输入灵活性（HEAVY/heavy 都能工作），脚本内部逻辑统一用小写比较。

## 5. 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 设计阶段 ADR 三条件过滤过于严格，导致本该记录的决策未被记录 | 中 | 中 | 设计阶段自检增加"ADR 评估"章节，列出被过滤的决策及理由 |
| CONTEXT.md 术语表维护负担过重，影响需求阶段效率 | 低 | 中 | LITE 模式下不强制维护 CONTEXT.md；术语表最小化原则（只记录领域特定术语） |
| 结构化调试 6 Phase 流程过长，对简单 bug 过度工程化 | 中 | 低 | 提供"快速调试"路径：单 Phase 跳过条件（可一步复现的 bug 可跳过 Phase 3-4） |
| 垂直切片任务拆分可能导致任务间逻辑耦合 | 低 | 低 | 允许共享 setup/teardown 任务作为独立前序任务 |
| 原型子阶段代码遗留风险 | 中 | 高 | 强制标注 + 完成后 grep 检查 + 闸门验证无遗留 |
| gate_check.py 改动影响现有 change 流程 | 低 | 高 | 改动后对所有已有归档目录运行回归测试 |

## 6. 既有架构对齐

- 触碰模块：
  - `references/stages/` 四个阶段文件（0,1,2,3）
  - `references/artifacts/` 两个工件模板（spec, task）
  - `references/scripts/` 两个闸门脚本
  - SKILL.md 主调度文件
- 禁动清单：
  - 不改动归档流程（special-flows.md）
  - 不改动验收阶段（7-acceptance.md）
  - 不改动测试阶段（4-test.md）
  - 不改动现有工件模板的核心字段（只新增，不删改）
- 沿用决策：
  - 沿用 Markdown + Python 的技术栈
  - 沿用 argparse + JSON 输出的脚本风格
  - 沿用中文注释和工件风格
  - 沿用 `<task>` XML 标签格式
  - 沿用交叉评审子代理协议
