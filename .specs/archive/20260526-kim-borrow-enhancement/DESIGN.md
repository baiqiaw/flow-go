# DESIGN — 借鉴 Kim_Decision/Meta_Kim 增强 flow-go（v2）

> change-id: `kim-borrow-enhancement`
> 复杂度: STANDARD
> 路径: 增量（本 change 是对 skill 自身的优化，不需要部署）

## 问题陈述

flow-go 已借鉴 Kim_Decision 三项直接机制（证据分级、验证假设、输出蒸馏），但 Kim 的核心方法论——"先问对问题再给方案"、"证据不足就停"、"避免正确废话"——尚未充分渗透到流程的深层设计。同时 Meta_Kim 的疤痕协议对长期工程质量有显著价值。

## 设计概要

4 项增量改动，每项独立可验收。改动范围**仅限于 references/ 下的 Markdown 文件 + SKILL.md 的引用更新**，不修改 Python 脚本。质量维度检查由 AI 在自检步骤中执行，不脚本化。

### 改动 1: 意图验证检查清单（Intent Verification）

**借鉴来源**: Kim_Decision 的九检查点决策框架

**问题**: 需求阶段的澄清门控（步骤 1）覆盖了 Why/Who/What/When done/How 五维度，但没有检查"这个想法值不值得做"。共情层关注理解用户，设计树追问关注设计决策分支，但缺少一个系统性的**可行性预检**——目标是否可测量、限制是否清楚、最小验证动作是什么。

**方案**: 在 0-requirement.md 的设计树追问（步骤 1C）之后、用户故事（步骤 4）之前，新增步骤 1D"意图验证"。不照搬 Kim 的 9 个检查点，只取 5 个最适配 flow-go 的：

| 检查项 | 检查什么 | 不通过处理 |
|--------|---------|-----------|
| 目标具体 | 目标有可测量的成功标准 | 追问量化指标 |
| 限制明确 | 技术约束/时间约束/资源约束已写清 | 追问限制条件 |
| 最小验证 | 能说出"今天最小的一步验证是什么" | 引导缩小范围 |
| 停止信号 | 能说出"什么信号说明该停" | 写入终止条件表 |
| 收益可感知 | 用户能描述"做完后的具体改善" | 追问收益场景 |

**触发条件**: STANDARD/HEAVY 复杂度必做，LITE 跳过（与设计树追问一致）。

**修改文件**:
- `references/stages/0-requirement.md`: 在步骤 1C 后新增步骤 1D
- `references/gate-rules.md`: 在假设闸门（§1.5）后新增意图闸门（§1.6）
- `references/anti-patterns.md`: 新增 req-07（意图未验证）

**不修改**: SKILL.md（改动 1 不影响主流程编排）、Python 脚本

### 改动 2: 闸门质量维度升级（纯 Markdown 规则）

**借鉴来源**: Kim_Decision 的五道闸门（启动/证据/逻辑/风险/决策）

**问题**: flow-go 的闸门主要检查**产物存在性**（文件是否存在、评审是否 PASS）。证据闸门（§1.4）是一个质量维度的开端，但只在设计阶段自检中触发。核心差距：闸门不检查"内容是否足够好"，只检查"文件是否存在"。

**方案**: 在 gate-rules.md 中新增**质量维度**章节（§1.8），定义为 AI 自检规则（非脚本化）。质量检查在阶段自检步骤中执行，不修改 gate_check.py。

| 闸门 | 质量检查规则 | 适用复杂度 |
|------|------------|-----------|
| 需求闸门 | AC 条目应含量化成功标准（> 50% 的 AC 包含可测量指标） | STANDARD/HEAVY |
| 需求闸门 | AC 应含 Given/When/Then 结构 | STANDARD/HEAVY |
| 设计闸门 | 关键决策应有 >=B 级证据支撑（> 50%） | STANDARD/HEAVY |
| 测试闸门 | 测试矩阵应覆盖边界场景（非仅 happy path） | STANDARD/HEAVY |

这些检查由 AI 在自检步骤中执行，不阻塞闸门通过，但输出质量警告。未来如需脚本化，可作为独立 change 实现。

**触发条件**: STANDARD/HEAVY 复杂度时在自检步骤中执行。LITE 跳过。

**修改文件**:
- `references/gate-rules.md`: 新增 §1.8 质量维度（信息性，不阻塞）

**不修改**: SKILL.md、阶段文件、Python 脚本（不修改 gate_check.py）

### 改动 3: 反"正确废话"检测

**借鉴来源**: Kim_Decision 的核心理念——"AI 最容易给出的不是错误答案，而是听起来对但无法执行的建议"

**问题**: 反模式清单覆盖了技术级错误（scope creep、skip-refactor 等），但缺少对**输出可执行性**的检测。需求文档可能出现"优化性能"这类不可操作的 AC，设计文档可能出现"使用合适的缓存策略"这类没有具体决策的描述。

**方案**: 在反模式清单中新增 3 条跨阶段可执行性反模式：

| ID | 反模式 | 检查什么 | 正确做法 |
|----|--------|---------|---------|
| cross-04-vague-ac | AC 包含模糊方向 | AC 含"优化/改进/提升"但无量化标准 | AC 必须含可测量的成功标准（"延迟 < 200ms"而非"性能更好"） |
| cross-05-vague-decision | 技术决策给出模糊建议 | 设计文档含"使用合适的/适当的/合理的"但无具体方案 | 给出具体选型（"使用 Redis 7.x LFU 淘汰"而非"使用合适的缓存"） |
| cross-06-no-next-action | 阶段输出缺少具体下一步 | 阶段完成输出无"用户现在该做什么" | 蒸馏输出必须包含具体下一步动作 |

**修改文件**:
- `references/anti-patterns.md`: 新增 3 条跨阶段反模式
- `references/distillation.md`: 强化"下一步"要求（引用 cross-06）
- `references/gate-rules.md` §4: 更新反模式速查摘要

**不修改**: SKILL.md、阶段文件、Python 脚本

### 改动 4: 疤痕协议（Scar Protocol）

**借鉴来源**: Meta_Kim 的疤痕协议——永久性失败记录

**问题**: flow-go 的进化分析侧重"信号检测 → 改进建议"，但缺少对**系统性治理失败**的持久化记录和预防规则提取。LESSONS 入库偏向经验教训，但缺少结构化的"上次为什么失败、以后怎么防"的预防性知识。

**方案**: 新增 `references/scars.md` 定义疤痕协议。

**疤痕格式**:
```markdown
---
id: YYYY-MM-type-short-desc
type: overstep | gate-bypass | process-gap | false-positive
trigger: 热修 | 闸门绕过 | 需求返工 | 审查 > 2 轮 | 活体验证 bug > 3
impact: none | degraded | recovered | critical
---

## 根因
<一句话描述系统性原因>

## 预防规则
<一条具体可执行的预防规则>
```

**目录结构**:
```
.specs/
├── <change-id>/          ← 归档时移动到 archive/
├── scars/                ← 全局目录，与 <change-id>/ 同级，归档不清理
│   └── YYYY-MM-type-short-desc.md
├── adr/                  ← 全局目录，归档不清理（已有）
├── CONTEXT.md            ← 全局文件（已有）
└── evolution/            ← 全局目录（已有）
```

**写入时机**（7-验收步骤 6 LESSONS 之后新增步骤 6A）:
- 热修发生 → 写入疤痕（type: gate-bypass）
- 审查 > 2 轮 → 检查是否系统性问题，是则写入（type: process-gap）
- 活体验证 bug > 3 → 写入（type: process-gap）
- 需求返工（设计阶段推翻需求） → 写入（type: overstep）

**扫描时机**（0-需求步骤 0 问题空间回退之后新增步骤 0A）:
- 读取 `.specs/scars/` 所有疤痕
- 按类型匹配当前变更特征
- 匹配到 → 输出警告：「⚠️ 历史疤痕：{预防规则}」

**与 LESSONS 的区别**:
- LESSONS = 经验教训（正向知识，"我们学到了什么"）
- Scars = 失败预防（反向知识，"我们曾在哪栽过跟头"）

**触发条件**: STANDARD/HEAVY 复杂度写疤痕。所有复杂度扫描疤痕。

**修改文件**:
- `references/scars.md`: 新建文件，定义疤痕格式和协议
- `references/stages/0-requirement.md`: 步骤 0 后新增步骤 0A（疤痕扫描）
- `references/stages/7-acceptance.md`: 步骤 6 后新增步骤 6A（疤痕写入）
- `references/stages/special-flows.md`: 热修流程中新增疤痕写入
- `SKILL.md`: 第七步状态更新中新增疤痕目录说明
- `references/gate-rules.md`: 新增 §5 疤痕协议（信息性扫描，不阻塞）
- `references/INDEX.md`: 新增 scars.md 条目

---

## 不做的事情（显式排除）

| 不做 | 原因 |
|------|------|
| 质量维度脚本化（gate_check.py --quality） | 语义级 Markdown 内容检查需大量 NLP 逻辑，当前阶段纯 Markdown 规则由 AI 执行更务实。未来可独立 change 脚本化 |
| 合约化工作流（JSON 合约定义） | 工程量过大，与当前 gate_check.py 架构差异大 |
| 多视角分析（七层透镜） | 设计阶段的 ADR 已有选项对比机制，新增七层分析增加认知负担但收益不明确 |
| Hook 自动化守卫扩展 | 需要 Claude Code hooks 机制支持，不是 skill 层面的改动 |
| 四层架构分离 / 八元代理 | 方向性差异，flow-go 的 6 角色 8 阶段体系已稳定 |

## 文件变更清单

| 文件 | 变更类型 | 改动量 |
|------|---------|--------|
| `references/stages/0-requirement.md` | 修改（新增步骤 0A、1D） | ~40 行 |
| `references/stages/7-acceptance.md` | 修改（新增步骤 6A） | ~15 行 |
| `references/stages/special-flows.md` | 修改（热修新增疤痕写入） | ~10 行 |
| `references/gate-rules.md` | 修改（新增 §1.6 意图闸门、§1.8 质量维度、§5 疤痕协议、反模式速查更新） | ~55 行 |
| `references/anti-patterns.md` | 修改（新增 req-07、cross-04/05/06） | ~20 行 |
| `references/distillation.md` | 修改（引用 cross-06） | ~3 行 |
| `references/scars.md` | **新建** | ~60 行 |
| `SKILL.md` | 修改（状态更新新增疤痕目录说明） | ~5 行 |
| `references/INDEX.md` | 修改（新增 scars.md 条目） | ~2 行 |

总改动量: ~210 行（新增 + 修改），**不涉及 Python 脚本修改**。

## AC（验收标准）

| # | AC | 验证方式 |
|---|-----|---------|
| 1 | STANDARD/HEAVY 需求阶段有步骤 1D 意图验证（含 5 个检查项的表格），LITE 跳过标记存在 | 读取 `0-requirement.md` 步骤 1D 内容，确认表格有 5 行 + LITE 跳过声明 |
| 2 | gate-rules.md 有 §1.8 质量维度章节（含 4 条规则），标注"信息性不阻塞" | 读取 `gate-rules.md` §1.8 内容，确认有 4 行规则表 + "信息性"标注 |
| 3 | anti-patterns.md 包含 cross-04/05/06 三条可执行性反模式（各有 ID、反模式、检查什么、正确做法） | 读取 `anti-patterns.md` 跨阶段章节，确认 3 条各有完整四列 |
| 4 | references/scars.md 存在，包含疤痕格式（frontmatter 3 字段 + 根因 + 预防规则）和完整协议 | 读取 `scars.md`，确认格式模板和写入/扫描时机说明 |
| 5 | 7-acceptance.md 有步骤 6A 疤痕写入，含 4 种触发场景 | 读取 `7-acceptance.md` 步骤 6A 内容，确认 4 种 trigger |
| 6 | 0-requirement.md 有步骤 0A 疤痕扫描，含读取/匹配/警告 3 步 | 读取 `0-requirement.md` 步骤 0A 内容 |
| 7 | special-flows.md 热修流程包含疤痕写入步骤 | 读取 `special-flows.md` 热修流程，确认包含疤痕写入步骤 |
| 8 | 回归测试全部通过 | `pytest tests/` 0 失败 |

## 验证假设

| # | 假设 | 证据级别 | 验证方式 | 验证阶段 | 推翻信号 |
|---|------|---------|---------|---------|---------|
| 1 | 意图验证不会显著增加需求阶段交互轮次 | C | 对比加入前后的平均提问数 | 3-开发 | 需求阶段交互 > 8 轮 |
| 2 | 质量警告不会造成告警疲劳 | C | 统计警告命中率 | 5-审查 | 警告忽略率 > 80% |
| 3 | 疤痕扫描对新 change 有实际预防价值 | D | 记录疤痕被命中的次数（每 2 个 change 中间回顾） | 7-验收 | 2 个 change 后 0 次命中 + 无合理解释 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 步骤膨胀导致需求阶段过重 | 中 | 中 | LITE 跳过所有新步骤（1D、0A 扫描仍执行但不写） |
| 疤痕目录持续膨胀 | 低 | 低 | 7-验收步骤 6A 中可清理 > 90 天的 none-impact 疤痕 |
| 质量警告误报 | 中 | 低 | 纯信息性不阻塞，由 AI 判断而非脚本硬判 |
