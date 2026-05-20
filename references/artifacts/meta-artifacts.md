# 元数据工件模板

> STATE.md / CONTEXT.md / LESSONS.md / ARCHIVE-INDEX.md / evolution/ — 跨变更持久化文件。

---

## STATE.md（项目根目录，跨变更）

### Schema

| 字段 | 必填 | 格式 | 默认值 | 说明 |
|------|------|------|--------|------|
| 活跃 Change | 是 | `<kebab-case-id>` 或 `无` | `无` | 当前正在进行的 change-id。归档/废弃后清空 |
| 当前阶段 | 是 | `<N>-<name>` 或 `无` | `无` | N 为 0-7，name 为阶段中文名（如 `3-开发`） |
| 当前任务 | 是 | `<task-id>` 或 `无` | `无` | 当前正在执行或下一个要执行的任务 ID |
| 中断任务 | 是 | `<task-id>` 或 `无` | `无` | 非空时回溯流程优先处理。仅 3-开发阶段写入 |
| 阶段进度 | 否 | `步骤 N: <简述>` 或 `无` | `无` | 非开发阶段的轻量级检查点。进入时写入当前步骤号+简述，阶段完成时清空 |
| 更新时间 | 是 | `YYYY-MM-DD` | 创建当天 | 用于回溯时判断搁置时长（30 天/60 天阈值） |

### 格式约束

1. 文件编码 UTF-8，首行必须是 `# STATE.md — flow-go 状态文件`
2. 字段使用 Markdown 标题 + 列表格式（非 YAML），确保人可读、AI 可 grep
3. 所有字段必须存在，不允许缺字段。无值时填 `无`
4. `活跃 Change` 值必须对应 `.specs/<id>/` 目录存在
5. `当前阶段` 值必须在 `0-需求` / `1-设计` / `2-任务` / `3-开发` / `4-测试` / `5-审查` / `6-部署` / `7-验收` 中取值
6. `当前任务` 和 `中断任务` 值必须对应 TASK.md 中的 task id（如有活跃 change）
7. 同一 task-id 不得同时出现在 `当前任务` 和 `中断任务`

### 完整性校验（回溯流程入口时执行）

- [ ] 文件存在且非空
- [ ] 首行包含 `STATE.md`
- [ ] 5 个字段全部存在（grep 5 个字段名）
- [ ] `活跃 Change` ≠ `无` → `.specs/<id>/` 目录存在
- [ ] `当前阶段` ≠ `无` → 值在 8 个合法阶段名中
- [ ] `中断任务` ≠ `无` → `当前任务` ≠ `中断任务`
- [ ] `更新时间` 格式为 YYYY-MM-DD

校验不通过时：输出具体缺失/不一致项，提示用户修复。不阻塞流程（降级为"无状态"模式，等同于新项目）。

### 模板

```markdown
# STATE.md — flow-go 状态文件

## 活跃 Change
- 无

## 当前阶段
- 无

## 当前任务
- 无

## 中断任务
- 无

## 阶段进度
- 无

## 更新时间
- YYYY-MM-DD
```

---

## CONTEXT.md（.specs/CONTEXT.md，跨变更）

```markdown
# CONTEXT — 项目上下文

## 域语言
| 术语 | 含义 | 英文标识 |
|------|------|---------|

## 已锁决策
| 决策 | 结论 | 理由 | 日期 |
|------|------|------|------|

## 默认偏好
- 代码语言 / 框架：<...>
- 测试框架：<...>
- 部署平台：<...>

## 已有抽象索引
| 能力 | 位置 | 用法 |
|------|------|------|

## 禁止清单
- <AI 不许触碰的文件 / 模块 / 模式>
```

---

## LESSONS.md（.specs/LESSONS.md，跨变更）

```markdown
# LESSONS — 失败经验知识库

> 开发员开工前必扫此文件。热修/审查/验收阶段均可提名新条目。

## 提名条件
满足任一即入库：
- 同一方案失败 ≥ 2 次
- 修复耗时 > 30 分钟
- 导致回滚或热修
- 热修流程中发现的根因模式
- 交叉评审经过 2+ 轮才通过的设计/实现问题

## 条目

### L-001 <场景简述>
- **触发关键词**：<grep 用，如 "migration" / "auth" / "deploy">
- **场景**：<什么情况下遇到的>
- **教训**：<学到了什么>
- **状态**：active / resolved
- **提名来源**：<change-id> + <task-id>
- **日期**：<YYYY-MM-DD>

### L-002 <场景简述>
...
```

---

## ARCHIVE-INDEX.md（.specs/archive/ARCHIVE-INDEX.md）

```markdown
# ARCHIVE INDEX — 归档索引

> 归档时自动维护，回溯时可选读取。不需要手动编辑。

## 归档统计
- 正常归档：N 个
- 废弃归档：N 个
- 最近归档：<date>-<id>
- 最早归档：<date>-<id>

## 归档清单

### 正常完成
| 归档目录 | Change-ID | 完成阶段 | 归档日期 | 保留状态 |
|----------|-----------|---------|---------|---------|
| 2026-05-14-user-auth | user-auth | 7-验收 | 2026-05-14 | 保留 |

### 废弃
| 归档目录 | Change-ID | 废弃原因 | 归档日期 | 保留状态 |
|----------|-----------|---------|---------|---------|
| 2026-04-01-old-api | old-api | 需求变更 | 2026-04-01 | 可清理 |

## 清理策略
- 默认保留期限：90 天
- 超期标记：`保留状态` 列标记为"可清理"
- 清理方式：手动确认后删除（不自动删除）
- 清理触发：用户说"清理归档" / 回溯流程超期提醒时
```

---

## evolution/（.specs/evolution/，进化引擎数据）

```markdown
# 进化引擎数据目录

> 由 evolution_signal.py + evolution_reflect.py 自动维护。
> 7-验收阶段和热修事后补齐时自动生成。

## 目录结构
.specs/evolution/
├── <change-id>-signals.json      # 信号检测报告
├── <change-id>-hypotheses.json   # 反思假设报告
├── <change-id>-capture.json      # CAPTURE 策略报告（健康评分≥8时）
└── strategies.jsonl              # 策略库（每行一个 JSON 策略）

## 信号报告格式（JSON）
{
  "change_id": "xxx",
  "date": "2026-05-16",
  "strong_signals": [{"type": "review_rework", "level": "strong", "evidence": ["..."]}],
  "medium_signals": [{"type": "tool_pitfall", "level": "medium", "evidence": ["..."]}],
  "should_reflect": true,
  "gate_passed": true
}

## 假设报告格式（JSON）
{
  "change_id": "xxx",
  "hypotheses": [
    {
      "id": "H20260516001",
      "origin": "FIX",
      "parent_hypothesis_id": ["H20260515002"] | null,
      "root_cause": "阶段指南中质量标准定义不够具体",
      "action_type": "modify_stage",
      "target_file": "references/stages/",
      "confidence": 0.80,
      "risk": "medium",
      "auto_approve_eligible": false,
      "proposed_change": "[evolution] ..."
    }
  ],
  "insights": [
    {
      "id": "INS-20260516-modify_stag",
      "source_hypothesis_ids": ["H20260514001", "H20260515002", "H20260516001"],
      "trigger_count": 3,
      "root_cause": "...",
      "advice": "..."
    }
  ],
  "auto_approve": [...],
  "needs_approval": [...]
}

## 策略库格式（strategies.jsonl，每行一个 JSON）
{"strategy_id":"S-20260516-xxx","change_id":"xxx","task_type":"feature|bugfix|refactor|doc","approach":"成功做法描述","score":85,"evidence":["verify 首次通过"],"origin":"CAPTURE","health_score":8.5,"created_at":"..."}
```

**策略打分规则**：
- 基础分 = health_score × 10（8.0→80）
- 交叉评审 1 轮通过 +8，2 轮 +2
- verify 首次通过 +5
- 上限 100 分

**策略复用**：3-开发阶段 grep strategies.jsonl，按 task_type 匹配取 score 最高的 1-2 条参考

---

## TRACE.md（.specs/<id>/TRACE.md，归档时生成）

轨迹记录，归档时由 trace_collector.py 自动生成。

### 格式

```markdown
# TRACE — <change-id>

## 阶段流转
| 阶段 | 角色 | 关键决策 | 闸门阻断 | 耗时估算 |
|------|------|---------|---------|---------|
| 0-需求 | 产品经理 | <决策摘要> | 0 | — |
| 1-设计 | 技术经理 | <决策摘要> | 0 | — |
| ... | ... | ... | ... | ... |

## 健康评分
- 总分：<N>/10
- 各维度：<列出>

## 标签
- 变更类型：<type>
- 复杂度：<level>
- 阶段瓶颈：<stage 或 null>
- 回溯次数：<N>
- 涉及文件数：<N>
- 跨子系统：<是/否>

## 实际结果
- outcome：<success/degraded/hotfixed/abandoned/null>
- 检测时间：<timestamp 或 "待标记">

## 状态快照
- 当前阶段：<阶段名>
- 阶段进度：<进度描述>
```

### 完整性校验（归档流程入口时执行）

- [ ] 文件存在且非空
- [ ] 首行包含 `TRACE`
- [ ] 包含 `阶段流转` 章节（含表头行）
- [ ] 包含 `健康评分` 章节
- [ ] 包含 `标签` 章节
- [ ] 包含 `实际结果` 章节

---

## traces.jsonl（.specs/traces.jsonl，跨变更累积）

机器可读轨迹记录，每次归档时由 trace_collector.py 追加一条。

### 记录格式

```json
{
  "change_id": "<change-id>",
  "timestamp": "<ISO8601 本地偏移>",
  "path": [0, 1, 2, 3, 4, 5, 6, 7],
  "path_mode": "full|incremental|shortest",
  "complexity": "LITE|STANDARD|HEAVY",
  "decisions": [
    {"stage": 0, "summary": "<决策摘要>", "type": "scope|architecture|task|implementation|review_fix"}
  ],
  "gate_blocks": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "6": 0, "7": 0},
  "health_score": 7.8,
  "health_dimensions": {
    "ac_coverage": 0.85,
    "test_completeness": 0.70,
    "review_efficiency": 0.80,
    "code_quality": 0.75,
    "boundary_hygiene": 0.90,
    "doc_completeness": 0.85,
    "resource_efficiency": 0.65
  },
  "manual_interventions": 0,
  "files_touched": 15,
  "tags": {
    "change_type": "feature",
    "complexity": "HEAVY",
    "bottleneck_stage": null,
    "rollback_count": 0,
    "files_touched": 15,
    "cross_subsystem": true
  },
  "outcome": null,
  "outcome_timestamp": null
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| change_id | string | 关联的 Change-ID |
| timestamp | string | 采集时间（ISO8601 本地时区偏移） |
| path | int[] | 经过的阶段序列 |
| path_mode | string | full=完整路径 / incremental=已完成阶段 / shortest=最小路径 |
| complexity | string | 复杂度级别 |
| decisions | array | 各阶段关键决策 |
| decisions[].stage | int\|null | 阶段编号 |
| decisions[].summary | string | 决策摘要（≤100 字） |
| decisions[].type | string | scope / architecture / task / implementation / review_fix |
| gate_blocks | object | 各阶段闸门阻断次数（轮次 - 1） |
| health_score | float\|null | 健康评分 |
| health_dimensions | object | 各维度评分（0-1 范围） |
| manual_interventions | int | 人工干预次数 |
| files_touched | int | 涉及文件数 |
| tags | object | 标签集合 |
| outcome | string\|null | success / degraded / hotfixed / abandoned / null |
| outcome_timestamp | string\|null | outcome 标记时间 |

### 完整性校验（gap_analyzer 使用前执行）

- [ ] 文件存在且非空
- [ ] 每行可解析为合法 JSON
- [ ] 每条记录包含 change_id / timestamp / path / path_mode / complexity 字段
- [ ] path_mode 在 full / incremental / shortest 中取值
- [ ] complexity 在 LITE / STANDARD / HEAVY 中取值

---

## EVOLUTION-WEEKLY-YYYYMMDD.md（.specs/evolution/EVOLUTION-WEEKLY-YYYYMMDD.md）

飞轮巡检周报，由手动触发（`飞轮巡检`）或周期触发（`/loop 7d`）生成。

### 格式

```markdown
# 飞轮周报 — YYYY/MM/DD

## 报告周期
- 起始：YYYY-MM-DD
- 截止：YYYY-MM-DD

## 归档统计
- 归档数量：N 个
- 平均健康评分：N.N / 10
- 复杂度分布：LITE N / STANDARD N / HEAVY N

## 健康评分趋势
| 周次 | 评分 | 变化 | 归档数 |
|------|------|------|--------|
| W1 | 7.2 | — | 2 |
| W2 | 7.8 | +0.6 | 3 |

## Top-3 薄弱切片（来自 gap_analyzer.py）
| 排名 | 维度 | 切片 | 偏差 | 关联教训 |
|------|------|------|------|---------|
| 1 | complexity | HEAVY | -2.0 | L-003 |
| 2 | change_type | refactor | -1.5 | — |
| 3 | bottleneck_stage | 4-测试 | -1.2 | — |

## 权重校准建议（来自 health_calibration.py）
| 维度 | 当前权重 | 建议权重 | 相关性 |
|------|---------|---------|--------|
| ac_coverage | 0.22 | 0.28 | 0.82 |
| doc_completeness | 0.10 | 0.06 | 0.20 |

## 新增 LESSONS 候选
| 编号 | 归因 | 建议 | 需确认 |
|------|------|------|--------|
| INS-001 | HEAVY 任务测试不充分 | 增加 HEAVY 类型强制测试轮次 | 是 |

## 策略捕获记录
| 策略 ID | 类型 | 做法 | 评分 |
|---------|------|------|------|
| S-001 | feature | 先写 verify 再写实现 | 88 |

## 下一步建议
1. <基于薄弱切片的改进行动>
2. <基于权重校准的调整建议>
3. <基于 LESSONS 候选的流程优化>
```

### 完整性校验

- [ ] 文件名包含有效日期（YYYYMMDD）
- [ ] 包含「报告周期」章节
- [ ] 包含「健康评分趋势」章节（含表头行）
- [ ] 包含「Top-3 薄弱切片」章节
- [ ] 包含「下一步建议」章节
