---
name: flow-go
description: >
  6 角色 8 阶段 AI 开发流程编排。输入 go 即可自动路由到下一步。
  角色包括：产品经理、项目经理、技术经理、开发员、测试员、运维。
  阶段流程：需求→设计→任务→开发→测试→审查→部署→验收。
  MUST trigger when the user says: "go", "/go", "继续", "下一步", "next",
  "新需求", "设计", "拆任务", "开发", "测试", "审查", "部署", "验收",
  "归档", "archive", "收工", "这个做完了",
  "废弃", "放弃", "abandon", "cancel",
  "排队", "pipeline", "backlog",
  "中断", "暂停", "interrupt", "并行", "parallel",
  "清理归档", "归档维护",
  "热修", "hotfix", "紧急修复",
  "回溯", "recall", "接着上次", "resume",
  "保存", "save", "整理", "neat", "同步", "sync up", "tidy up docs", "update memory",
  "clean up docs", "/sync", "/neat", "同步一下", "整理文档", "整理一下",
  "更新记忆", "梳理一下", "收尾",
  "进化分析", "反思一下", "检查进化", "进化信号", "进化状态", "归因",
  "飞轮巡检", "飞轮报告", "周报", "标记结果", "更新 outcome",
  "轨迹分析", "gap 分析", "校准评分", "校准权重",
  或任何描述新功能/新需求的短语（且当前无活跃 change）。
  Cross-platform: works on Claude Code, OpenAI Codex, OpenCode, and OpenClaw.
---

# Flow-Go — 6 角色 × 8 阶段流程编排

> **使用方式**：输入 `go` 或任何阶段关键词，AI 自动路由到正确的阶段和角色。

## 流程全景

```
[0-需求] → [1-设计] → [2-任务] → [3-开发] → [4-测试] → [5-审查] → [6-部署] → [7-验收]
  产品经理     技术经理    项目经理     开发员     测试员     技术经理     运维     产品经理+项目经理
```

特殊流程：`归档`（任意阶段完成）/ `废弃`（放弃）/ `热修`（紧急）/ `回溯`（恢复）/ `整理`（内建知识库同步）/ `归档维护`（清理）

> **权衡声明**：flow-go 偏向严谨而非速度。LITE 模式可简化闸门，但涉及安全/跨模块/数据迁移的变更仍需完整流程。简单任务可酌情简化，但"太简单不需要走流程"本身是最常见的返工原因。

---

## 前置动作 · 用户输入记录

**在执行任何步骤之前，先将当前用户输入追加到 `.specs/<id>/user-inputs.jsonl`**。

这是每轮对话的初始动作（横切关注点），不是编号步骤。类似于角色红线，贯穿所有阶段。

- 仅在 STATE.md 有活跃 Change（索引表非空）时执行（无活跃 Change 时跳过）
- 格式（每行一个 JSON 对象，append-only）：
  ```json
  {"ts":"2026-05-21T14:30:00","change_id":"xxx","stage":"3-开发","input":"用户原始输入"}
  ```
- `change_id`：从 STATE.md 活跃 Change 索引表读取
- `stage`：从 `.specs/<id>/STATE.md` `当前阶段` 字段读取
- `input`：用户消息原文（保留原文，不做加工）
- `.specs/<id>/` 目录已存在（有活跃 Change 时），直接追加
- 每条用户消息只追加一次
- 此数据用于验收阶段的反馈分类和 SUGGEST 进化路径，详见 `references/scripts/feedback_classifier.py`

---

## 第一步 · 读状态

1. 尝试读项目根目录 `STATE.md`。不存在 → 新项目，跳过
2. **旧格式检测与迁移**：检查 STATE.md 中 `## 活跃 Change` 下的内容——若为非表格的单行文本（如 `- xxx`）且非 `无`，判定为旧格式。旧格式迁移步骤：
   - (a) 读取旧格式所有字段（活跃 Change、当前阶段、当前任务、中断任务、Pipeline 待续、并行 Change、阶段进度、更新时间）
   - (b) 生成新格式 STATE.md：活跃 Change 改为表格格式（含 change-id / 阶段 / 最后更新 列），保留 Pipeline 待续和更新时间
   - (c) 创建 `.specs/<id>/STATE.md`：写入当前阶段、当前任务、中断任务、阶段进度、更新时间
   - (d) 旧格式的 `并行 Change` 字段内容迁移为索引表的多行
   - (e) 迁移完成后输出「🔄 旧格式 STATE.md 已自动迁移为新格式」
3. 执行完整性校验：调用 `python3 references/scripts/validate_state.py --state-file STATE.md --specs-dir .specs/`。脚本不可用时回退到 grep `references/artifacts/meta-artifacts.md` 的「完整性校验」清单。校验不通过 → 输出脚本返回的具体问题，降级为"无状态"模式（等同新项目）。如脚本返回 `fixes` 字段非空 → 额外提示「可自动修复缺失字段，回复"修复"即可」
4. 校验通过后解析活跃 Change 索引表：
   - **活跃数 = 0**：无活跃 change，后续路由按"无活跃 change"处理
   - **活跃数 = 1**：自动读 `.specs/<id>/STATE.md` 获取当前阶段/当前任务/中断任务/阶段进度。将 change-id 写入会话上下文供后续阶段使用。**零额外操作**——用户体验与旧格式完全一致
   - **活跃数 > 1**：列出所有活跃 change（change-id + 阶段），用 AskUserQuestion 让用户选择要操作的 change → 读选中的 `.specs/<id>/STATE.md` → 将 change-id 写入会话上下文
5. 选定 change 后检查：`中断任务` 非空 → 优先级最高，走回溯流程
6. Worktree 检查：读取 `.specs/<id>/STATE.md` 的 `worktree_path` 字段。非空 → 检查 worktree 目录是否存在（`test -d <path>`）。存在 → 记录到会话上下文。不存在但路径有记录 → 输出「⚠️ worktree 已丢失：<path>，建议手动恢复或废弃」
7. 尝试读 `.specs/CONTEXT.md`。不存在 → 棕地项目提醒可跑 intel-scan，不强制
   - 读取 `.specs/CONTEXT.md`（如存在）→ 将术语定义注入到会话上下文，后续所有阶段使用规范术语
   - 读取 `.specs/adr/` 目录（如存在且非空）→ 统计 ADR 数量，提示"已有 N 条架构决策记录，设计阶段将自动检查"
8. `Pipeline 待续` 非空且活跃 Change 表为空 → 优先输出「📋 Pipeline 待续：{change-id}，要开始吗？」。用户确认"开始"后执行启动流程：清空 `Pipeline 待续` 字段 → PIPELINE.md 中该 change 标记为 `active` → 创建 `.specs/<id>/` 目录 + `.specs/<id>/STATE.md` → 更新 STATE.md 索引表添加行 → 路由到 0-需求

## 第二步 · 加载配置（可选）

读取用户偏好配置（按优先级）：
1. 项目级 `.flowgo-config`（项目根目录）
2. 用户级 `~/.flowgo-config`（HOME 目录）
3. 内置默认值

**支持的配置项**：
| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `test_rounds` | 3 | 4-测试阶段单轮修复上限 |
| `test_depth` | standard | 4-测试阶段默认深度（smoke / standard / deep） |
| `max_files_per_task` | 10 | 3-开发阶段单任务改动文件上限 |
| `auto_sync` | true | 决策信号自动触发知识库受作用域同步 |
| `priority_framework` | MoSCoW | 2-任务阶段默认优先级框架（auto=按决策树自动选择，MoSCoW/WSJF/RICE/ICE/MCDA=强制指定） |
| `explain_level` | default | 解释详细度（default / terse） |
| `evolution_mode` | auto | 进化分析模式（auto=自动触发 / off=关闭） |
| `complexity_threshold` | 5 | blast-radius 文件数阈值 |
| `bitter_pill_auto` | true | 归档后自动触发苦丸审计 |
| `preflight_check` | true | 2-任务阶段启用预检环（反幻觉+粒度+上下文预算） |
| `context_budget_mode` | auto | 上下文预算模式（auto=自动估算 / manual=手动填写 / off=关闭） |
| `flywheel_min_samples` | 3 | 飞轮分析最小轨迹样本数 |
| `flywheel_gap_threshold` | 1.5 | Gap 分析偏差阈值（分） |
| `flywheel_outcome_check` | true | 是否自动检测归档后 outcome |
| `flywheel_outcome_days` | 7 | outcome 自动检测窗口（天） |
| `context_summarize` | false | 是否默认启用上下文摘要（false=全文加载，true=摘要加载） |
| `trace_auto_collect` | true | 归档时是否自动采集轨迹 |
| `user_input_capture` | true | 是否记录用户输入到 user-inputs.jsonl |

**配置格式**（YAML，每行一个键值对）：
```yaml
test_rounds: 3
test_depth: standard
max_files_per_task: 10
auto_sync: true
priority_framework: MoSCoW  # 或 auto / WSJF / RICE / ICE / MCDA
explain_level: default
preflight_check: true
context_budget_mode: auto
flywheel_min_samples: 3
flywheel_gap_threshold: 1.5
flywheel_outcome_check: true
flywheel_outcome_days: 7
context_summarize: false
trace_auto_collect: true
user_input_capture: true
```

### Terse 模式压缩规则

> 当 `explain_level: terse` 时，所有角色输出遵循以下压缩规则。借鉴 caveman 方法论——保留全部技术实质，只砍填充词。

**删除项**：
- 冠词（一个/这个/那个）
- 填充词（其实/实际上/简单来说/基本上/当然）
- 寒暄（好的/当然可以/没问题/很高兴）
- 模糊修饰（大概/可能/也许）
- 长同义词替换（用"大"不用"广泛的"，用"改"不用"实现一个解决方案来"）

**保留项**：
- 技术术语精确不变（变量名/API名/配置项原文）
- 代码块完整不变
- 错误信息原文引用
- 数据/指标精确值

**输出格式**：`[对象] [动作] [原因]。[下一步]。`

**示例**：
- 不是："好的！这个问题的原因可能是 React 组件在每次渲染时创建了新的内联对象引用，导致 props 比较失败触发重新渲染。建议使用 useMemo 来缓存这个对象。"
- 而是："内联 obj prop → 新 ref → 重新渲染。用 `useMemo`。"

**安全自动退出**：遇到以下场景时自动退出 terse 模式，恢复完整表达：
- 安全警告（密钥泄露/权限问题/数据风险）
- 破坏性操作确认（删除/覆盖/重置）
- 多步骤序列（顺序混乱会误读）
- 用户请求澄清

退出时输出完整信息，事后自动恢复 terse。

## 第三步 · 意图路由

按以下表格匹配用户输入（**取最先命中**）：

| 用户输入特征 | 路由到 | 角色 |
|---|---|---|
| `继续` / `接着上次` / `resume` | 回溯流程 | 自动 |
| `执行 T<NN>` / `跑 T<NN>` | 3-开发（指定任务） | 开发员 |
| `审查` / `review` / `代码审查` | 5-审查 | 技术经理 |
| `测试` / `写测试` / `QA` | 4-测试 | 测试员 |
| `部署` / `上线` / `发布` / `deploy` | 6-部署 | 运维 |
| `验收` / `UAT` / `交付` | 7-验收 | 产品经理+项目经理 |
| `拆任务` / `排期` / `规划` | 2-任务 | 项目经理 |
| `设计` / `架构` | 1-设计 | 技术经理 |
| `需求` / `requirement` | 0-需求 | 产品经理 |
| `归档` / `archive` / `收工` / `这个做完了` | 归档流程 | 当前阶段角色 |
| `废弃` / `放弃` / `abandon` / `cancel` | 废弃流程 | 项目经理 |
| `排队` / `pipeline` / `backlog` | 排队管理流程 | 自动 |
| `中断` / `暂停` / `interrupt` | 中断流程 | 当前阶段角色 |
| `并行` / `parallel` / `同时开始` | 并行启动流程 | 自动 |
| `飞轮巡检` / `飞轮报告` / `周报` | 飞轮巡检流程 | 自动 |
| `标记结果` / `更新 outcome` | outcome 标记流程 | 自动 |
| `轨迹分析` / `gap 分析` | 运行 gap_analyzer.py | 自动 |
| `校准评分` / `校准权重` | 运行 health_calibration.py | 自动 |
| `清理归档` / `归档维护` / `archive cleanup` | 归档维护流程 | 运维 |
| `热修` / `hotfix` / `紧急修复` | 热修流程 | 开发员→技术经理 |
| `原型` / `prototype` | 1-设计（原型子流程） | 技术经理 |
| `回溯` / `recall` | 回溯流程 | 自动 |
| `整理` / `neat` / `同步` | 加载 `references/sync-workflow.md` 执行全量同步 | — |
| `保存` / `save` | 写 PROGRESS.md + 更新 STATE.md | 当前角色 |
| `进化分析` / `反思一下` / `检查进化` / `进化信号` / `归因` | 运行 evolution_signal + evolution_reflect，展示假设和归因摘要 | 自动 |
| `进化状态` | 显示进化触发条件状态（健康趋势 / 归因频率 / 历史数据量） | 自动 |
| `go` / `下一步` / `next` | STATE 有活跃变更 → 读 per-change STATE 获取当前阶段 → 当前阶段下一步；无 → 0-需求 | 自动 |
| `/lite` | 强制设置当前 change 复杂度为 LITE，跳转到当前阶段 | 开发员 |
| `/heavy` | 强制设置当前 change 复杂度为 HEAVY，跳转到当前阶段 | 开发员 |
| 任何新事物描述（当前无活跃 change） | 0-需求（自动生成 change-id） | 产品经理 |
| 模糊不清 | 反问：「新需求 / 继续上次 / 审查测试 / 别的？」 | — |

**并行模式 AFK 优先调度**：当并行模式（parallel）启动时，读取 TASK.md 各 task 的 mode 属性（afk/hitl/colab），AFK 任务优先分配给独立 agent 执行，HITL 任务留在当前会话等待人工决策。mode 属性未设置时默认为 colab。

### 路由决策可视化

> 完整路由流程图见 `references/routing-diagram.md`（按需加载）。

### Worktree 进入

路由确定后、闸门检查前，检查目标 change 的 worktree 状态：
- per-change STATE.md 的 `worktree_path` 非空且 worktree 目录存在 → 调用 EnterWorktree（path: <worktree_path>）进入 worktree
- `worktree_path` 为空 → 留在主仓库（阶段 0-1 不需要 worktree）
- 非空但目录不存在 → 输出「⚠️ worktree 已丢失：<path>」，建议用户手动恢复或废弃

## 第三步半 · 复杂度分级

路由确定后、闸门检查前，自动判定当前 change 的复杂度级别：

1. 调用 `python3 references/scripts/complexity_classifier.py --description "<用户描述>" --project-dir <项目根> --specs-dir .specs/<change-id>`
2. 用户可通过 `/lite` 或 `/heavy` 快捷指令覆盖自动判定
3. 分级结果在角色声明中展示（第五步）
4. 复杂度影响闸门检查的严格程度（LITE 简化闸门，HEAVY 加强审查）

## 第四步 · 闸门检查

<HARD-GATE>
进入阶段前**必须**验证前置条件。不满足则停下来，引导用户补齐。
每个 change 都走完整闸门流程——无论是单行 bugfix 还是大型 feature。"简单"变更恰恰是未审查假设导致返工最多的地方。不允许用"这个太简单不需要走 X 阶段"跳步。

常见合理化陷阱（全部驳回）：
- "就改个按钮颜色，不需要设计" → 颜色变更可能影响设计系统一致性
- "bugfix 不需要需求文档" → 没有 AC 就没有回归测试依据
- "单文件改动直接开发" → 不理解上下文的修改是 new bug 的温床
- "热修可以跳过审查" → 热修审查是防止生产事故的最后一道防线
</HARD-GATE>

> 闸门检查规则（含分类标签 gate/safety）见 `references/gate-rules.md` §1-2（grep 加载）。
> 脚本化验证：`python3 references/scripts/gate_check.py --stage <N> --change-id <id> --specs-dir .specs/<id> --complexity <level> [--categories gate]`

**CONTEXT/ADR 补充检查**（不阻塞闸门通过，仅作为信息报告）：
- 阶段 0（STANDARD/HEAVY）：如 REQUIREMENT.md 术语表有内容但 `.specs/CONTEXT.md` 不存在 → 输出提示「建议创建 CONTEXT.md 记录项目术语」
- 阶段 1（HEAVY）：检查设计阶段是否完成了 ADR 三条件评估（非阻塞）
- 这些检查由 `gate_check.py` 自动执行，脚本不可用时跳过

**增量闸门模式**：同一阶段内第二次及后续闸门检查，只验证增量部分：
- 读 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段
- 已在进度中标记完成的工件 → 跳过
- 新增/修改的工件 → 执行完整验证
- 阶段转换（进入新阶段）→ 忽略增量模式，执行完整闸门检查

### 闸门后续 · Handoff 检查（仅阶段转换时执行）

Handoff 检查在**首次阶段转换**时执行，验证上游上下文是否已传递。跨会话恢复时跳过——工件仍在即说明上下文已传递，重复验证无增量价值，只浪费 token。

**判断依据**：本次进入阶段是否由「上一阶段完成」触发？
- **是**（阶段转换）：闸门检查 → Handoff 检查 → 角色声明 → 阶段步骤
- **否**（会话恢复 / 回溯 / 热修）：闸门检查 → 角色声明 → 阶段步骤

阶段转换时，grep `references/handoff-protocols.md` 中对应阶段的「TO 确认」项，逐条验证。任一不满足 → 停下，回溯上游角色补齐。

## 第五步 · 角色声明

路由确定后，输出角色声明：

```
✅ 路由：<阶段名>
✅ Change-ID：<id>（新需求场景尚未生成时写"待生成"）
✅ 复杂度：<LITE / STANDARD / HEAVY>
✅ 当前角色：<角色名>
✅ 角色红线：<一句话提醒该角色的禁止事项>
✅ 阶段锚点：<对应当前阶段的口诀，见下表>
✅ 第一动作：<具体下一步>
✅ 项目记忆：{如 CONTEXT.md 存在："N 个领域术语" + "M 条 ADR" / "无"}
```

### 阶段锚点口诀

| 阶段 | 角色 | 锚点口诀 |
|------|------|---------|
| 0-需求 | 产品经理 | 不确定就问，不猜不假设 |
| 1-设计 | 技术经理 | 每个决策有替代方案 |
| 2-任务 | 项目经理 | 每个 task 可独立验证 |
| 3-开发 | 开发员 | 每行改动追溯到需求 |
| 4-测试 | 测试员 | 按验收标准写用例，不改实现 |
| 5-审查 | 技术经理 | 0 严重项才过关 |
| 6-部署 | 运维 | 部署前有回滚方案 |
| 7-验收 | 产品经理 | 逐条对照 AC 验收 |

## 角色约束速查

> 角色约束规则见 `references/gate-rules.md` §3（grep 加载）。

## 阶段反模式速查

> 完整反模式清单（含原子化 id）见 `references/anti-patterns.md`。快速自检摘要见 `references/gate-rules.md` §4。

## 第六步 · 加载执行

按阶段名加载 `references/stages/<N>-<name>.md` 对应文件，按其步骤执行。
需要工件模板时加载 `references/artifacts/<category>.md` 对应文件。

**加载映射**：
| 路由目标 | 加载文件 | 工件模板文件 |
|---------|---------|-------------|
| 0-需求 | `stages/0-requirement.md` | `artifacts/spec-artifacts.md`（CHANGE/REQUIREMENT） |
| 1-设计 | `stages/1-design.md` | `artifacts/spec-artifacts.md`（DESIGN） |
| 2-任务 | `stages/2-task.md` | `artifacts/task-artifacts.md`（TASK） |
| 3-开发 | `stages/3-develop.md` | `artifacts/task-artifacts.md`（SUMMARY/PROGRESS） |
| 4-测试 | `stages/4-test.md` | `artifacts/quality-artifacts.md`（TEST） |
| 5-审查 | `stages/5-review.md` | `artifacts/quality-artifacts.md`（REVIEW） |
| 6-部署 | `stages/6-deploy.md` | `artifacts/deploy-artifacts.md`（DEPLOY） |
| 7-验收 | `stages/7-acceptance.md` | `artifacts/deploy-artifacts.md`（UAT） |
| 热修/归档/废弃/回溯/归档维护 | `stages/special-flows.md`（grep 对应流程） | 按需（归档→`meta-artifacts.md`，废弃→`deploy-artifacts.md`） |
| worktree 相关 | grep 加载 `references/worktree-lifecycle.md` 对应流程 | — |

**Token 预算**：按阶段按需加载 reference 文件（禁止整读）。每个阶段仅加载 `stages/<N>-<name>.md` + 对应 `artifacts/<category>.md`，需额外参考时才 grep 其他文件。评审子代理调用不计入主代理 token 预算。

### 阶段内精炼环（3-开发阶段，STANDARD/HEAVY）

每个 task 代码编写完成后、写 SUMMARY.md 之前，自动执行精炼环：

1. **功能不变检查**：diff 仅改变实现方式，未改变输入输出行为
2. **反模式清零**：对照阶段反模式速查表「3-开发」清单，逐条自检
3. **直觉检验**：资深工程师看了会说"太复杂了"吗？→ 是则简化
4. **清晰度提升**：至少一处改善（减少嵌套/消除冗余/改善命名/移除不必要的注释）
5. **边界卫生**：改动文件均在 TASK.md write_files 范围内

全项通过 → 写 SUMMARY.md；任一不通过 → 修复后重入精炼环。

LITE 模式跳过精炼环。

### 阶段内验证闭环

以下场景必须执行验证闭环（自我验证子步骤）：

**开发 task 完成 → 精炼环通过后**：
1. 确认功能不变：grep diff 确认无行为变更（仅实现变更）
2. 确认 verify 通过：重新运行 TASK.md 中的 verify 命令
3. 记录到 SUMMARY.md：在"自检"章节追加「验证闭环：功能不变 ✅ / verify ✅」

**审查修复完成 → 进入下一阶段前**：
1. 确认修复有效：针对每个修复项重新验证
2. 确认无新增问题：修复未引入新的严重项
3. 记录到 REVIEW.md：在评审矩阵后追加「验证闭环：修复有效 ✅ / 无新增严重项 ✅」

### Skill 链式调用白名单

<EXTREMELY-IMPORTANT>
flow-go 流程中**只允许调用以下 skill**。未列出的 skill 一律禁止调用，即使用户的请求看起来相关。

| 流程位置 | 允许调用的 skill | 说明 |
|---------|-----------------|------|
| 3-开发（遇到 bug/异常） | `superpowers:systematic-debugging` | 仅在遇到真实 bug 时，不用于需求澄清 |

**内建同步能力**：7-验收完成后、归档/废弃完成后、决策信号触发时，flow-go 自动执行知识库同步（全量或受作用域），无需调用外部 skill。同步工作流详见 `references/sync-workflow.md`，路径速查见 `references/agent-paths.md`，变更映射见 `references/sync-matrix.md`。

**禁止调用**：`frontend-design`、`mcp-builder`、`superpowers:brainstorming`、`superpowers:writing-plans`、`superpowers:test-driven-development` 及其他未列出的 skill。这些 skill 与 flow-go 的角色红线冲突（角色分工已内置，不需要外部 skill 介入）。
</EXTREMELY-IMPORTANT>

### MCP 扩展点（可选）

flow-go 默认以文件驱动（STATE.md / .specs/），不依赖外部 MCP。以下 MCP 集成为可选增强，需要用户配置后才能使用。

| MCP Server | 适用阶段 | 用途 | 回退方案 |
|-----------|---------|------|---------|
| GitHub MCP | 3-开发 / 5-审查 / 6-部署 | 自动创建 issue 关联 change、PR 创建与链接、CI 状态检查 | 手动 git 操作 + 文件记录 |
| Jira MCP | 0-需求 / 2-任务 / 7-验收 | 需求同步到 Jira issue、任务与 sprint 关联、验收状态更新 | 纯文件工件（REQUIREMENT/TASK/UAT） |
| Slack MCP | 7-验收后 | 验收结果通知团队频道 | 手动复制 UAT 摘要 |

**MCP 命令示例**：

```bash
# ── GitHub MCP（3-开发阶段）──
# 创建 issue 关联 change
mcp__github__create_issue owner="myorg" repo="myrepo" title="[CH-001] 用户登录功能" body="关联 Change: CH-20240315-001"

# 创建 PR 并关联
mcp__github__create_pull_request owner="myorg" repo="myrepo" title="feat: 用户登录功能 (CH-001)" head="feat/login" base="main"

# 检查 CI 状态
mcp__github__pull_request_read method="get_check_runs" owner="myorg" repo="myrepo" pullNumber=42

# ── Jira MCP（0-需求阶段）──
# 需求同步到 Jira Epic
mcp__jira__create_issue project="PROJ" summary="用户登录功能" type="Epic" description="Change-ID: CH-20240315-001"

# 任务关联到 Sprint
mcp__jira__create_issue project="PROJ" summary="T01-后端登录API" type="Story" parent="PROJ-100"

# 验收后更新状态
mcp__jira__transition_issue issue="PROJ-100" status="Done"

# ── Slack MCP（7-验收后）──
# 验收结果通知
mcp__slack__post_message channel="#team" text="✅ CH-001 用户登录功能验收通过，评分 85/100 (A级)"
```

**使用原则**：
- MCP 数据为辅、文件为主。STATE.md（项目级索引）+ `.specs/<id>/STATE.md`（change 级详情）始终是唯一状态源
- MCP 不可用时自动回退到文件方案，不阻塞流程
- MCP 操作需在阶段步骤中显式声明（如「可选：如已配置 GitHub MCP，创建 issue 关联 change」）

## 第七步 · 状态更新

阶段完成（或产出工件）后，更新状态文件：

- **阶段内高频更新**（阶段进度、当前任务）：写入 `.specs/<change-id>/STATE.md` 的对应字段
- **阶段转换**：写入 `.specs/<change-id>/STATE.md` 的当前阶段字段 + 更新 STATE.md 索引表中该 change 的阶段和最后更新列
- **worktree 追踪**：worktree 创建时，per-change STATE.md 的 `worktree_path` 写入路径值。归档/废弃清理后，`worktree_path` 清为 `无`
- **启动新 change**：创建 `.specs/<id>/STATE.md` + 在 STATE.md 索引表添加新行
- **归档**：从 STATE.md 索引表移除该 change 行 + 删除 `.specs/<id>/STATE.md`（归档/废弃流程自身步骤中完成，此处不再重复）
- **轨迹采集触发**（配置项 `trace_auto_collect` 控制，默认 true）：归档流程步骤 4.5 已在 `special-flows.md` 中定义，此处仅声明配置项引用。设为 false 时跳过轨迹采集
- **中断流程**（用户请求暂停/切换 change 时触发）：中断流程在 `special-flows.md` 中定义。状态更新规则：PIPELINE.md 中状态改为 `interrupted`，`.specs/<change-id>/STATE.md` 更新 `中断任务` 字段记录中断阶段
- **Pipeline 衔接**（归档流程完成后触发）：归档流程内部步骤 8.5 已在 `special-flows.md` 中定义（读 PIPELINE.md → 找 pending → 写 Pipeline 待续 → 提示用户）。步骤 7 此处声明：归档流程完成后如 `Pipeline 待续` 已被写入，在状态更新时输出衔接提示
- **中断流程**（用户请求暂停/切换 change 时触发）：中断流程在 `special-flows.md` 中定义。STATE.md 更新规则：PIPELINE.md 中状态改为 `interrupted`，STATE.md 更新 `中断任务` 字段记录中断阶段，`活跃 Change` 可清空
- **CONTEXT/ADR 持久化检查**：设计阶段完成时，如产出了新 ADR（`.specs/adr/` 下有新文件），输出「📜 新增 N 条 ADR：{ADR 标题列表}」。归档时 `.specs/CONTEXT.md` 和 `.specs/adr/` 不删除（跨 change 持久化），仅清理 `.specs/<id>/` 下的 change 级文件
- **决策同步检查**：grep 本阶段「决策信号」，逐条检查产出工件是否匹配
  - 有匹配 → 输出「🔄 决策同步：N 条新决策，执行受作用域同步」然后加载 `references/sync-workflow.md` 执行受作用域同步
  - 无匹配 → 跳过
  - 7-验收阶段：固定加载 `references/sync-workflow.md` 执行全量同步（验收 = 交接里程碑）
- **自动进化触发**（配置项 `evolution_mode` 控制，默认 `auto`，设为 `off` 则跳过全部进化分析）：归档完成后按健康评分走双路径
  - **CAPTURE 路径**（成功经验）：读 `health-history.jsonl` 最近一条，评分 ≥ 8.0 → 执行 `evolution_reflect.py --mode capture --specs-dir .specs/<id> --health-score <分>` → 成功策略存入 `.specs/evolution/strategies.jsonl` → 输出「🏆 策略已捕获：{approach}（评分 {score}）」
  - **FIX 路径**（失败改进）：以下条件满足任一即触发
    1. 连续 3 个 Change 健康评分下降（读 `health-history.jsonl` 最近 3 条）
    2. 同一归因标签在最近 5 个 Change 中出现 ≥3 次（读 `.specs/evolution/` 下的信号历史）
  - FIX 触发时 → 输出「🧬 进化信号已触发：{原因}，正在运行进化分析」→ 执行 `evolution_signal.py` → `evolution_reflect.py --mode reflect` → 展示假设和归因摘要
  - 有顿悟时 → 额外输出「💡 顿悟：{root_cause}（已出现 N 次）→ 建议：{advice}」，请用户确认是否写入 LESSONS.md
  - **BITTER PILL 路径**（规则自审计）：归档后自动执行 `python3 references/scripts/bitter_pill_audit.py --skill-dir <flow-go skill 目录> --output .specs/<id>/BITTER-PILL.md` → 产出 KEEP/REVIEW/CANDIDATE 审计报告 → CANDIDATE 项需用户逐条确认 → 输出「💊 苦丸审计完成：KEEP N / REVIEW N / CANDIDATE N」
  - **SUGGEST 路径**（改进建议，归档后触发，与 CAPTURE/FIX 同级）：
    - 触发条件：`.specs/evolution/skill-feedback.jsonl` 存在且含 `processed=false` 的条目
    - 路径行为：
      1. 读取未处理的 skill 反馈，按频率排序
      2. 运行 `evolution_reflect.py --mode suggest --feedback .specs/evolution/skill-feedback.jsonl --output .specs/evolution/<id>-suggestions.json`
      3. 生成改进假设报告
      4. 展示假设摘要，请用户逐条确认
      5. 用户确认的改进 → 记录到建议列表，由用户手动执行修改
      6. 全部处理完成后，将 skill-feedback.jsonl 中的对应条目标记为 `processed=true`
    - **安全原则**：SUGGEST 路径不自动修改 SKILL.md 或 references/ 下的任何文件
    - **SUGGEST 不可自动执行的症状清单**（出现任一条即需用户逐条确认）：
      1. 建议删除现有闸门检查或 HARD-GATE 机制
      2. 建议修改角色红线的核心边界
      3. 建议增加新的 Skill 链式调用白名单条目
      4. 建议绕过 STATE.md 状态管理直接操作文件
- **飞轮巡检**（手动触发：`飞轮巡检` / `飞轮报告` / `周报`；周期触发：`/loop 7d "运行 flow-go 飞轮巡检"`）：
  1. 运行 `gap_analyzer.py` → 输出 Gap 报告
  2. 运行 `health_calibration.py` → 输出校准报告（样本 ≥ `flywheel_min_samples` 时）
  3. 检查跨 Change 聚合顿悟 → 复用 `evolution_reflect.py` 写入逻辑
  4. 生成 `EVOLUTION-WEEKLY-YYYYMMDD.md`（模板见 `meta-artifacts.md`）
  5. 顿悟候选请用户确认

## 自检（产出路由声明前）

- [ ] 已读 STATE.md（如果存在）
- [ ] 已按路由表匹配意图
- [ ] 新 CHANGE 已自动生成 change-id（如适用）
- [ ] 闸门前置条件已验证
- [ ] 角色声明包含红线提醒
- [ ] 决策同步检查已执行（有信号已触发 / 无信号已跳过）
