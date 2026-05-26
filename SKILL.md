---
name: flow-go
description: >
  6 角色 8 阶段 AI 开发流程编排。输入 go 即可自动路由到下一步。
  角色包括：产品经理、项目经理、技术经理、开发员、测试员、运维。
  阶段流程：需求→设计→任务→开发→测试→审查→部署→验收。
  MUST trigger when the user says any of these:
  - 流程推进：go / 继续 / 下一步 / next
  - 阶段直达：新需求 / 设计 / 拆任务 / 开发 / 测试 / 审查 / 部署 / 验收
  - 特殊流程：热修 / hotfix / 修复bug / 修bug / 归档 / 废弃 / 回溯 / 接着上次 / resume
  - 管理操作：排队 / 中断 / 并行 / 保存 / 整理 / 同步 / 进化分析 / 飞轮巡检 / 周报
  - 收尾操作：收工 / 收尾 / 归档维护 / 归因 / 校准
  - 或任何描述新功能/新需求的短语（且当前无活跃 change）。
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

## 路径模式阶段转换

路径模式在 0-需求阶段步骤 9 确定后写入 `.specs/<id>/STATE.md` 的 `路径模式` 字段。后续所有阶段转换和闸门检查都依赖此字段。

| 路径模式 | 阶段序列 | 跳过的阶段 | 适用条件 |
|---------|---------|-----------|---------|
| 完整 | 0→1→2→3→4→5→6→7 | 无 | 新功能 / 多文件变更 / 架构影响 |
| 增量 | 0→1→2→3→4→5→7 | 6-部署 | 已有 CI/CD 管线的内部工具 / 非生产环境部署 |
| 最短 | 0→3→4→7 | 1-设计 / 2-任务 / 5-审查 / 6-部署 | 单文件改动 / 配置调整 / typo 修复 |

**阶段转换规则**（当用户说 "go"/"下一步"/"next" 且当前阶段完成时）：
1. 从 `.specs/<id>/STATE.md` 读取 `路径模式` 字段
2. 查上表得到当前路径的阶段序列
3. 在序列中找到当前阶段的下一阶段 → 路由到该阶段
4. 当前阶段已是序列末尾（如 7-验收）→ 路由到归档流程

**跳过阶段不执行**：路径模式中跳过的阶段不进入、不加载、不执行闸门检查。闸门检查仅对序列中实际经过的阶段生效。

**路径模式详细定义**：`references/path-modes.md`（含闸门适配规则和工件简化方案）。

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
   - **活跃数 = 1**：自动读 `.specs/<id>/STATE.md` 获取当前阶段/路径模式/当前任务/中断任务/阶段进度。将 change-id 和路径模式写入会话上下文供后续阶段使用。**零额外操作**——用户体验与旧格式完全一致
   - **活跃数 > 1**：列出所有活跃 change（change-id + 阶段），用 AskUserQuestion 让用户选择要操作的 change → 读选中的 `.specs/<id>/STATE.md` → 将 change-id 写入会话上下文
5. 选定 change 后检查：`中断任务` 非空 → 优先级最高，走回溯流程
6. Worktree 检查：读取 `.specs/<id>/STATE.md` 的 `worktree_path` 字段。非空 → 检查 worktree 目录是否存在（`test -d <path>`）。存在 → 记录到会话上下文。不存在但路径有记录 → 输出「⚠️ worktree 已丢失：<path>，建议手动恢复或废弃」
7. 尝试读 `.specs/CONTEXT.md`。不存在 → 棕地项目提醒可跑 intel-scan，不强制
   - 读取 `.specs/CONTEXT.md`（如存在）→ 将术语定义注入到会话上下文，后续所有阶段使用规范术语
   - 读取 `.specs/adr/` 目录（如存在且非空）→ 统计 ADR 数量，提示"已有 N 条架构决策记录，设计阶段将自动检查"
8. `Pipeline 待续` 非空且活跃 Change 表为空 → 加载 `references/common/pipeline-continuation.md`（trigger=recall-start）

## 第二步 · 加载配置（可选）

读取用户偏好配置（按优先级）：项目级 `.flowgo-config` → 用户级 `~/.flowgo-config` → 内置默认值。

> 完整配置项清单和默认值见 `references/configuration.md`。关键配置项：`explain_level`（terse 时加载 `references/terse-mode.md`）、`evolution_mode`（off 时跳过进化分析）、`guard_enabled`（3-开发阶段回归防护）。

## 第三步 · 意图路由

<HARD-GATE>
**流程入口硬约束**：一旦本 skill 被加载，用户输入**必须**经过路由表匹配后才能决定行动。禁止读取用户输入中的任务描述后直接执行——无论任务看起来多简单，都必须走 第一步（读状态）→ 本步（路由）→ 第四步（闸门）→ 第五步（角色声明）→ 第六步（执行）的完整链路。用户输入中的描述部分仅作为流程输入参数传递给对应阶段，不作为直接执行指令。
</HARD-GATE>

**复合输入解析**：用户输入可能包含流程启动词 + 阶段关键词 + 描述内容（如 "go 修复bug:登录白屏" 或 "热修 生产环境 OOM"）。解析步骤：

1. **提取路由关键词**：在用户输入中搜索路由表所有关键词（含复合模式如 `go 热修`），按路由表顺序取最先命中
2. **保留描述内容**：关键词之外的部分作为该流程的输入描述（冒号后、关键词后的文本），传递给对应阶段的步骤使用
3. **`go` 本身是流程启动信号，不是路由目的地**：`go` 单独出现时按 STATE 当前阶段走下一步；`go` 后跟阶段关键词时，阶段关键词决定路由

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
| `热修` / `hotfix` / `紧急修复` / `修复bug` / `修bug` / `go 热修` / `go 修复` / `go hotfix` | 热修流程 | 开发员→技术经理 |
| `原型` / `prototype` | 1-设计（原型子流程） | 技术经理 |
| `回溯` / `recall` | 回溯流程 | 自动 |
| `整理` / `neat` / `同步` | 加载 `references/sync-workflow.md` 执行全量同步 | — |
| `保存` / `save` | 写 PROGRESS.md + 更新 STATE.md | 当前角色 |
| `进化分析` / `反思一下` / `检查进化` / `进化信号` / `归因` | 运行 evolution_signal + evolution_reflect，展示假设和归因摘要 | 自动 |
| `进化状态` | 显示进化触发条件状态（健康趋势 / 归因频率 / 历史数据量） | 自动 |
| `go` / `下一步` / `next` | STATE 有活跃变更 → 读 per-change STATE 获取当前阶段和路径模式 → 按路径模式阶段转换表确定下一阶段 → 路由到该阶段；当前阶段完成时同样按转换表跳转；无活跃变更 → 0-需求 | 自动 |
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
> 脚本化验证：`python3 references/scripts/gate_check.py --stage <N> --change-id <id> --specs-dir .specs/<id> --complexity <level> --path-mode <full|incremental|shortest> [--categories gate]`

**路径模式适配**：闸门检查必须读取 `.specs/<id>/STATE.md` 的 `路径模式` 字段，按 `references/path-modes.md` 的闸门适配规则执行：
- **最短路径**：阶段 3 仅需 CHANGE.md（含内联 AC）+ 代码提交（不检查 DESIGN.md / TASK.md）；阶段 4 仅需代码已提交（不检查 SUMMARY.md）；阶段 7 仅需 4-测试通过 + CHANGE.md AC 全部满足（不检查 DEPLOY.md / REVIEW.md）
- **增量路径**：阶段 1-5 闸门与完整路径相同；阶段 7 简化为不需要 DEPLOY.md
- **完整路径**：全部闸门与 gate-rules.md 表一致
- 路径模式中跳过的阶段不执行闸门检查（不进入 = 不检查）

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

### 阶段完成闸门（阶段转换前必检）

<HARD-GATE>
当前阶段转换到下一阶段前，必须验证当前阶段完成条件已全部满足。此闸门与「进入闸门」互补——进入闸门检查上游工件是否存在，完成闸门检查当前阶段自身是否真正完成（含交叉评审）。

**为什么需要这个闸门**：同一会话中完成阶段主体工作后，最常见的行为就是跳过自检和交叉评审直接进入下一阶段。这正是导致返工最多的捷径——"设计看起来没问题就直接拆任务"、"任务拆完了直接开发"。交叉评审的存在价值恰恰是在没有上下文偏见的全新视角下发现主代理遗漏的问题。

**检查时机**：用户说 go/下一步 且当前阶段主体工作已完成、即将转换到下一阶段时。

**检查流程**：
1. 读取当前阶段文件（`references/stages/<N>-<name>.md`）的「完成条件」
2. 逐条验证。重点：交叉评审（如阶段步骤包含）的报告已产出且 6 维全 PASS
2a. 验证无技术债残留（阶段 3 及后续）：检查 SUMMARY.md 无"已知问题"、TEST.md Bug 清单所有严重度 = 0、REVIEW.md 所有级别问题 = 0
3. 验证方式（阶段 0/1/2 文档评审）：检查 `<change-id>-REVIEW.md` 中是否存在当前阶段评审章节，且该章节的评审矩阵中 6 维全部为 PASS。阶段 3 代码评审产出在 `<task-id>-SUMMARY.md`，阶段 5 质量评审产出在 `REVIEW.md`——这两类评审的完成条件由各自阶段文件定义
4. 任一条件不满足 → 停下来完成缺失步骤，禁止转换到下一阶段

**禁止行为**（全部驳回）：
- "同一会话已完成主体工作" → 交叉评审的存在价值就是独立于主代理视角
- "用户已口头确认" → 口头确认不等于 6 维矩阵验证
- "设计/任务内容很简单" → 简单正是"不审查导致返工"的重灾区
- 阶段步骤未全部完成（含自检和交叉评审）时更新 STATE.md 到下一阶段
- 未验证 `<change-id>-REVIEW.md` 当前阶段评审 PASS 就转换阶段
- 阶段 3-开发及后续阶段：存在未清零的 bug/问题/技术债标记就转换到下一阶段——交叉评审循环必须达到 0 问题，门禁验证 0 问题状态
</HARD-GATE>

## 第五步 · 角色声明

路由确定后，输出角色声明：

```
✅ 路由：<阶段名>
✅ Change-ID：<id>（新需求场景尚未生成时写"待生成"）
✅ 路径模式：<完整 / 增量 / 最短>（新需求时写"待确定"）
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
| 5-审查 | 技术经理 | 所有级别问题 = 0 才过关 |
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
| common/ 引用 | special-flows.md 步骤内显式写明加载路径 | 按参数替换后执行 |

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
2. 确认无新增问题：修复未引入新的问题
3. 记录到 REVIEW.md：在评审矩阵后追加「验证闭环：修复有效 ✅ / 无新增问题 ✅」

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

flow-go 默认以文件驱动，不依赖外部 MCP。可选集成 GitHub / Jira / Slack MCP，需要用户配置后才能使用。

> 支持的 MCP Server、命令示例和使用原则见 `references/mcp-integration.md`。

核心原则：MCP 数据为辅、文件为主。MCP 不可用时自动回退到文件方案。

## 第七步 · 状态更新

阶段完成（或产出工件）后，更新状态文件：

- **阶段内高频更新**（阶段进度、当前任务）：写入 `.specs/<change-id>/STATE.md` 的对应字段
- **阶段转换**：写入 `.specs/<change-id>/STATE.md` 的当前阶段字段 + 更新 STATE.md 索引表中该 change 的阶段和最后更新列。**下一阶段由路径模式决定**（查本文件「路径模式阶段转换」表的阶段序列），不是固定 +1
- **worktree 追踪**：worktree 创建时，per-change STATE.md 的 `worktree_path` 写入路径值。归档/废弃清理后，`worktree_path` 清为 `无`
- **启动新 change**：创建 `.specs/<id>/STATE.md` + 在 STATE.md 索引表添加新行
- **归档**：从 STATE.md 索引表移除该 change 行 + 删除 `.specs/<id>/STATE.md`（归档/废弃流程自身步骤中完成，此处不再重复）
- **轨迹采集触发**（配置项 `trace_auto_collect` 控制，默认 true）：归档流程步骤 4.5 已在 `special-flows.md` 中定义，此处仅声明配置项引用。设为 false 时跳过轨迹采集
- **中断流程**（用户请求暂停/切换 change 时触发）：中断流程在 `special-flows.md` 中定义。状态更新：PIPELINE.md 状态改为 `interrupted`，`.specs/<change-id>/STATE.md` 更新 `中断任务` 字段，STATE.md `活跃 Change` 可清空
- **Pipeline 衔接**（归档流程完成后触发）：归档流程内部步骤 8.5 已在 `special-flows.md` 中定义。归档流程完成后如 `Pipeline 待续` 已被写入，在状态更新时输出衔接提示
- **CONTEXT/ADR 持久化检查**：设计阶段完成时，如产出了新 ADR（`.specs/adr/` 下有新文件），输出「📜 新增 N 条 ADR：{ADR 标题列表}」。归档时 `.specs/CONTEXT.md` 和 `.specs/adr/` 不删除（跨 change 持久化），仅清理 `.specs/<id>/` 下的 change 级文件。同理 `.specs/scars/` 也是全局持久化目录，归档不清理。疤痕协议详见 `references/scars.md`
- **决策同步检查**：grep 本阶段「决策信号」，逐条检查产出工件是否匹配
  - 有匹配 → 输出「🔄 决策同步：N 条新决策，执行受作用域同步」然后加载 `references/sync-workflow.md` 执行受作用域同步
  - 无匹配 → 跳过
  - **例外——归档/验收已内联同步**：归档流程步骤 9.6 和 7-验收步骤 8 已各自内联执行同步，不依赖此信号检查机制
- **自动进化触发**（配置项 `evolution_mode` 控制，默认 `auto`，设为 `off` 则跳过全部进化分析）：归档完成后走 CAPTURE / FIX / BITTER PILL / SUGGEST 四路径。详细触发条件和脚本参数见 `references/evolution-paths.md`
- **飞轮巡检**（手动触发：`飞轮巡检` / `飞轮报告` / `周报`）：运行 `gap_analyzer.py` + `health_calibration.py`，生成 `EVOLUTION-WEEKLY-YYYYMMDD.md`
- **轻量进化检查**（每个阶段完成时自动执行，不依赖归档）：检测 `user_correction` / `gate_blocked` 即时信号，检测到输出「⚡ 即时信号」，无信号静默跳过。不写文件、不调脚本
- **蒸馏输出**：阶段闸门通过后、状态更新前，对用户可见输出做蒸馏。内部过程（评审评分、自检清单、证据标注全文）保留在工件中，终端只展示：结论 + 关键风险（≤3 条）+ 下一步。蒸馏规则见 `references/distillation.md`

## 自检（产出路由声明前）

- [ ] 已读 STATE.md（如果存在）
- [ ] 已按路由表匹配意图
- [ ] 已读取路径模式（来自 `.specs/<id>/STATE.md` 的 `路径模式` 字段，新需求时为"待确定"）
- [ ] 新 CHANGE 已自动生成 change-id（如适用）
- [ ] 闸门前置条件已验证（按路径模式适配的闸门规则）
- [ ] 角色声明包含红线提醒
- [ ] 决策同步检查已执行（有信号已触发 / 无信号已跳过 / 归档或验收已内联同步）
