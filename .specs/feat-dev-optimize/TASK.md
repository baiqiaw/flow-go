# TASK — feat-dev-optimize

## 依赖图
T01 [P] → 无依赖
T03 [P] → 无依赖
T04 [P] → 无依赖
T02 → 依赖 T04（引用 cross-review-matrix.md 置信度引导机制）

## 并行分组
- 组 A [并行]：T01(small) + T03(small) + T04(small) — 三个独立文件修改
- 组 B：T02(small) — 依赖 T04 完成后的增强
- 全部 small 级别，无 large 任务

## 任务列表

<task id="T01" parallel="true" priority="must" type="refactor" mode="afk">
  <name>1-design.md 增加并行子代理探索步骤</name>
  <read_files>references/stages/1-design.md</read_files>
  <write_files>references/stages/1-design.md</write_files>
  <action>
在 1-design.md 的步骤 1 和步骤 2 之间插入步骤 1.5「并行子代理探索」。

插入内容要点：
1. 标题：1.5 **并行子代理探索**（STANDARD/HEAVY 必做，LITE 跳过）
2. dispatch 2-3 个 explorer 子代理（model: sonnet），每个聚焦不同维度：
   - explorer-1："找到与 [需求] 类似的功能，追踪完整实现链路，返回 5-10 个关键文件路径"
   - explorer-2："映射 [需求领域] 的架构层次和抽象，返回 5-10 个关键文件路径"
   - explorer-3（可选）："分析 [需求领域] 的测试模式和扩展点，返回 5-10 个关键文件路径"
3. 子代理返回后：合并文件列表去重 → 主代理逐个深度阅读 → 产出综合分析摘要
4. 降级规则：子代理失败 → 主代理单线程探索
5. 与上下游衔接：综合分析作为步骤 2（技术栈选型）的输入依据

同时更新自检清单：
1. 增加「并行探索已执行或已降级（STANDARD/HEAVY 时）」
2. 增加「备选方案章节已填写（STANDARD/HEAVY 时）」（来自 DESIGN.md 8.3 联动要求，因 T01 已写 1-design.md，在此任务一并处理避免并行写冲突）
  </action>
  <verify>grep -c "并行子代理探索" references/stages/1-design.md</verify>
  <done>1-design.md 包含步骤 1.5 并行探索定义、降级规则、LITE 跳过条件，自检清单已更新（含并行探索项和备选方案项）</done>
  <guard>grep -c "步骤 1.5" references/stages/1-design.md</guard>
  <depends_on></depends_on>
  <e2e_coverage>prompt 定义 → 自检清单 → 降级规则</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>独立修改单文件，可与其他 small 任务并行</agent_hint>
</task>

<task id="T02" parallel="false" priority="must" type="refactor" mode="afk">
  <name>5-review.md 增加并行 reviewer 模式</name>
  <read_files>references/stages/5-review.md, references/cross-review-matrix.md</read_files>
  <write_files>references/stages/5-review.md</write_files>
  <action>
增强 5-review.md 步骤 3（代码质量 6 维审查）为并行 reviewer 模式。

修改内容要点：
1. 在步骤 3 开头增加并行 reviewer dispatch 说明：
   dispatch 3 个 reviewer 子代理（model: sonnet），按矩阵 C 维度分组：
   | 子代理 | 覆盖维度 | prompt 聚焦 |
   | reviewer-1 | R1 认知过载 + R3 知识重复 | 单函数长度、嵌套层级、重复逻辑 |
   | reviewer-2 | R2 变更传播 + R4 偶然复杂 + 安全审查 | 越界改动、过度抽象、密钥泄露 |
   | reviewer-3 | R5 依赖混乱 + R6 领域扭曲 | import 方向、命名一致性 |
2. 每个 reviewer 输出格式含置信度列和严重度分组（Critical ≥90 / Important 80-89，仅 ≥80 才报告）
3. 合并去重规则：同一位置同一问题取最高置信度，按严重度排序后进入步骤 5
4. 降级规则：子代理失败 → 主代理按矩阵 C 完整 6 维单线程审查
5. 保留 HEAVY 模式现有的"dispatch 独立子 Agent 二次 cross-review"不变
  </action>
  <verify>grep -c "并行 reviewer" references/stages/5-review.md</verify>
  <done>5-review.md 步骤 3 包含并行 reviewer 分组表、置信度输出格式、合并去重规则、降级规则</done>
  <guard>grep -c "reviewer-1.*R1.*认知过载" references/stages/5-review.md || grep -c "并行 reviewer dispatch" references/stages/5-review.md</guard>
  <depends_on>T04</depends_on>
  <e2e_coverage>prompt 定义 → 分组表 → 合并规则 → 循环评审衔接</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>依赖 T04 完成后执行，修改单文件</agent_hint>
</task>

<task id="T03" parallel="true" priority="must" type="refactor" mode="afk">
  <name>spec-artifacts.md DESIGN.md 模板增加备选方案章节</name>
  <read_files>references/artifacts/spec-artifacts.md</read_files>
  <write_files>references/artifacts/spec-artifacts.md</write_files>
  <action>
在 spec-artifacts.md 的 DESIGN.md 模板中，于「4. ADR」之后、「5. 风险」之前插入「4.5 备选方案」章节。

新增模板内容：
```markdown
## 4.5 备选方案（STANDARD/HEAVY 必填，LITE 跳过）

### 方案 A：<名称>（推荐/备选）
- **描述**：<方案概述>
- **优点**：<...>
- **缺点**：<...>

### 方案 B：<名称>
- **描述**：<方案概述>
- **优点**：<...>
- **缺点**：<...>

**最终选择**：方案 <A/B>，理由：<...>
```

同步更新：
1. spec-artifacts.md 的 DESIGN.md 自检清单增加：「备选方案章节已填写（STANDARD/HEAVY 时至少 2 个方案对比）」
2. 此自检项对应 AC-3（LITE 跳过、STANDARD/HEAVY 至少 2 个方案）
  </action>
  <verify>grep -c "备选方案" references/artifacts/spec-artifacts.md</verify>
  <done>spec-artifacts.md DESIGN.md 模板包含「4.5 备选方案」章节（含方案 A/B 模板），自检清单已更新</done>
  <guard>grep -c "4.5 备选方案" references/artifacts/spec-artifacts.md</guard>
  <depends_on></depends_on>
  <e2e_coverage>模板章节 → 自检清单 → LITE 跳过标注</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>独立修改单文件，可与其他 small 任务并行</agent_hint>
</task>

<task id="T04" parallel="true" priority="must" type="refactor" mode="afk">
  <name>cross-review-matrix.md 增加置信度引导和 sonnet model</name>
  <read_files>references/cross-review-matrix.md</read_files>
  <write_files>references/cross-review-matrix.md</write_files>
  <action>
增强 cross-review-matrix.md 的子代理调用协议，加入置信度评分引导和 model 指定。

修改 3 处：

1. prompt 模板「约束」部分（在"不要修改任何文件"之后）新增：
```markdown
## 置信度评分
对每个潜在问题评分 0-100：
- 0-49：低置信度，大概率误报或不重要
- 50-79：中置信度，真实问题但不关键
- 80-89（Important）：高置信度，确认的真实问题
- 90-100（Critical）：极高置信度，必须修复

**仅报告置信度 ≥80 的问题。** 过滤掉低置信度发现以减少噪音。
```

2. prompt 模板「输出格式」的「发现问题」部分修改：
```markdown
### 发现问题
- Critical（置信度 ≥90）：
  - {文件:位置 — 问题描述 — 置信度 — 建议修复方向}
- Important（置信度 80-89）：
  - {文件:位置 — 问题描述 — 置信度 — 建议修复方向}
- {全 PASS 则写"无"}
```

3. 「子代理约束」部分新增：
```markdown
- 子代理 dispatch 时指定 **model: sonnet**（探索/评审任务不需要最强模型）
- 每个发现必须附带置信度评分（0-100），仅输出 ≥80 的发现
```

4. 「各阶段调用参数」表格新增「子代理 model」列，所有阶段行填 sonnet
  </action>
  <verify>grep -c "置信度评分" references/cross-review-matrix.md</verify>
  <done>cross-review-matrix.md prompt 模板含置信度引导、输出格式含严重度分组、子代理约束含 model: sonnet、调用参数表含 model 列</done>
  <guard>grep -c "≥80" references/cross-review-matrix.md</guard>
  <depends_on></depends_on>
  <e2e_coverage>prompt 增强 → 约束更新 → 参数表更新</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>独立修改单文件，可与其他 small 任务并行。T02 依赖本任务产出</agent_hint>
</task>
