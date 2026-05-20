# DESIGN — data-flywheel

## 0. 技术栈选定

| 候选 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| Python 标准库（argparse + json + os） | 与现有 12 个脚本完全一致；零依赖；跨平台 | 功能有限（无统计分析库） | ✅ 首选 |
| Python + statistics 标准库模块 | 内置 mean/stdev/correlation，满足基础统计 | 仍是标准库，无需额外安装 | ✅ 备选 |
| Python + numpy/pandas | 强大的统计分析能力 | 引入第三方依赖，违反 Principles | ❌ 排除 |

最终选择：**Python 标准库（含 statistics 模块）**。理由：与现有脚本风格一致，statistics 模块（Python 3.4+）提供 mean/stdev/correlation 等基础统计函数，满足闭环校准和 Gap 分析的需求，无需引入第三方依赖。

## 1. 架构图

```
                          ┌─────────────────────────────────────────────┐
                          │           数据飞轮架构                       │
                          └─────────────────────────────────────────────┘

  ┌──────────┐    ┌───────────────┐    ┌────────────────┐    ┌──────────────┐
  │  归档流程  │───▶│trace_collector│───▶│ traces.jsonl   │───▶│ gap_analyzer │
  │  (修改)   │    │   .py         │    │ (追加写入)      │    │   .py        │
  └──────────┘    └───────────────┘    │                │    └──────┬───────┘
       │                               │  ┌──────────┐  │           │
       │                               │  │outcome   │  │           ▼
       │                               │  │字段      │  │    ┌──────────────┐
       │                               │  └──────────┘  │    │  Gap 报告     │
       │                               └───────┬────────┘    │  (JSON)      │
       │                                       │              └──────────────┘
       │           ┌───────────────┐           │                       │
       │           │health_        │           │                       ▼
       │           │calibration.py │◀──────────┘              ┌──────────────┐
       │           └───────┬───────┘                          │ 飞轮巡检      │
       │                   │                                  │ (周报生成)    │
       │                   ▼                                  └──────────────┘
       │           ┌───────────────┐                                 │
       │           │ 权重调整建议   │                                 ▼
       │           │ (JSON)        │                          ┌──────────────┐
       │           └───────────────┘                          │ 跨 Change    │
       │                                                      │ 聚合顿悟     │
       │                                                      └──────┬───────┘
       │                                                             │
       │                                                             ▼
       │                                                      ┌──────────────┐
       │                                                      │ LESSONS.md   │
       │                                                      │ (写入)       │
       │                                                      └──────────────┘
       │
       │    ┌───────────────────┐    ┌────────────────────────┐
       └───▶│artifact_format_   │───▶│ Token 效率报告 (JSON)   │
            │analyzer.py        │    └────────────────────────┘
            └───────────────────┘

  ┌──────────────────────────────────────────────────────────────────────────┐
  │                        上下文优化（并行轨道）                              │
  │                                                                          │
  │  ┌───────────┐    ┌───────────────────┐    ┌──────────────────────────┐  │
  │  │阶段指南    │───▶│context_summarizer │───▶│ 阶段摘要（stdout）        │  │
  │  │(含需求清单)│    │   .py             │    └──────────────────────────┘  │
  │  └───────────┘    └───────────────────┘                                   │
  └──────────────────────────────────────────────────────────────────────────┘
```

## 2. 数据流

### 2.1 执行轨迹采集流

```
归档流程触发
    │
    ▼
trace_collector.py --specs-dir .specs/<id> --change-id <id>
    │
    ├── 读取 STATE.md（获取阶段流转信息）
    ├── 读取 .specs/<id>/ 下所有工件（提取关键决策）
    ├── 读取 health-history.jsonl 最近一条（获取健康评分）
    ├── 读取 CHANGE.md（提取变更类型、复杂度）
    │
    ├── 生成 .specs/<id>/TRACE.md（人类可读版）
    │
    └── 追加到 .specs/traces.jsonl（机器可读版）
```

### 2.2 Gap 分析流

```
gap_analyzer.py --specs-dir .specs
    │
    ├── 读取 traces.jsonl（全部轨迹）
    ├── 按 6 个标签维度分片
    ├── 计算各切片平均健康评分
    ├── 识别偏差 > 1.5 分的切片
    ├── 读取 LESSONS.md（关联薄弱环节）
    │
    └── 输出 Gap 报告（JSON 到 stdout）
```

### 2.3 健康评分闭环流

```
health_calibration.py --specs-dir .specs
    │
    ├── 读取 traces.jsonl（含 outcome 字段）
    ├── 过滤 outcome != null 的记录
    ├── 按 7 个健康维度分别计算与 outcome 的相关性
    ├── 比较当前权重 vs 相关性建议权重
    │
    └── 输出校准报告（JSON 到 stdout）
```

### 2.4 飞轮巡检流

```
手动触发：/进化分析 或 /飞轮巡检
周期触发：CronCreate /loop 7d "运行 flow-go 飞轮巡检"
    │
    ├── 运行 gap_analyzer.py → 获取薄弱切片
    ├── 运行 health_calibration.py → 获取权重建议
    ├── 检查跨 Change 聚合顿悟条件
    │   └── 同一归因标签最近 5 Change 出现 ≥3 次 → 触发顿悟
    ├── 生成 EVOLUTION-WEEKLY-YYYYMMDD.md
    │
    └── 顿悟需用户确认后写入 LESSONS.md
```

## 3. API 设计（新增脚本接口）

### 3.1 trace_collector.py

```
用法：
  python3 trace_collector.py --specs-dir .specs/<id> --change-id <id> \
    [--health-score 7.8] [--complexity STANDARD] [--path-mode full]

参数：
  --specs-dir     : spec 目录路径（必选）
  --change-id     : Change-ID（必选）
  --health-score  : 健康评分（可选，默认从 health-history.jsonl 读取）
  --complexity    : 复杂度 LITE/STANDARD/HEAVY（可选，默认从 CHANGE.md 推断）
  --path-mode     : 路径模式 full/incremental/shortest（可选，默认 full）
  --tags          : 额外标签 JSON（可选，如 '{"change_type":"feature"}'）
  --output-trace  : TRACE.md 输出路径（可选，默认 <specs-dir>/TRACE.md）
  --output-jsonl  : traces.jsonl 路径（可选，默认 <specs-dir>/../traces.jsonl）

输入：
  - STATE.md
  - .specs/<id>/ 下所有工件
  - health-history.jsonl
  - CHANGE.md

输出：
  - TRACE.md（人类可读版）
  - traces.jsonl 追加一条记录

traces.jsonl 记录格式：
{
  "change_id": "data-flywheel",
  "timestamp": "2026-05-19T10:00:00+08:00",
  "path": [0, 1, 2, 3, 4, 5, 6, 7],
  "path_mode": "full",
  "complexity": "HEAVY",
  "decisions": [
    {"stage": 0, "summary": "确认为单个大型 change", "type": "scope"},
    {"stage": 1, "summary": "选用 Python 标准库含 statistics", "type": "architecture"}
  ],
  "gate_blocks": {"0": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
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

退出码：0=成功，1=参数错误，2=工件缺失
```

### 3.2 artifact_format_analyzer.py

```
用法：
  python3 artifact_format_analyzer.py --skill-dir <flow-go skill 目录>
    [--format json|text]

参数：
  --skill-dir  : flow-go skill 根目录（必选）
  --format     : 输出格式 json/text（可选，默认 json）

输入：
  - references/artifacts/*.md（工件模板文件）
  - references/stages/*.md（阶段指南，用于交叉引用字段使用情况）

输出（JSON）：
{
  "templates": [
    {
      "file": "spec-artifacts.md",
      "artifacts": ["CHANGE.md", "REQUIREMENT.md", "DESIGN.md"],
      "total_fields": 25,
      "used_downstream": 18,
      "unused_fields": ["术语表（DESIGN.md 从未被下游阶段引用）", "..."],
      "redundant_patterns": [
        "CHANGE.md 范围排除与 REQUIREMENT.md Out of Scope 语义重叠",
        "..."
      ],
      "token_efficiency": 0.72,
      "suggestions": ["建议将 CHANGE.md 范围排除合并到 REQUIREMENT.md", "..."]
    }
  ],
  "summary": {
    "total_templates": 5,
    "avg_efficiency": 0.68,
    "top_redundancy": "CHANGE.md 范围排除 vs REQUIREMENT.md Out of Scope"
  }
}

退出码：0=成功，1=参数错误
```

### 3.3 health_calibration.py

```
用法：
  python3 health_calibration.py --specs-dir .specs [--min-samples 5]

参数：
  --specs-dir    : 项目 spec 根目录（必选）
  --min-samples  : 最小样本数（可选，默认 5，不足则输出警告）

输入：
  - .specs/traces.jsonl（含 outcome 字段的记录）
  - .specs/evolution/health-history.jsonl（历史健康评分）

输出（JSON）：
{
  "sample_size": 12,
  "outcome_distribution": {"success": 8, "degraded": 2, "hotfixed": 1, "abandoned": 1},
  "correlations": {
    "ac_coverage": {"correlation": 0.82, "current_weight": 0.22, "suggested_weight": 0.28},
    "test_completeness": {"correlation": 0.65, "current_weight": 0.18, "suggested_weight": 0.20},
    "review_efficiency": {"correlation": 0.30, "current_weight": 0.13, "suggested_weight": 0.08},
    "code_quality": {"correlation": 0.71, "current_weight": 0.15, "suggested_weight": 0.18},
    "boundary_hygiene": {"correlation": 0.55, "current_weight": 0.12, "suggested_weight": 0.12},
    "doc_completeness": {"correlation": 0.20, "current_weight": 0.10, "suggested_weight": 0.06},
    "resource_efficiency": {"correlation": 0.15, "current_weight": 0.10, "suggested_weight": 0.08}
  },
  "suggestions": [
    "ac_coverage 与实际结果高度相关（r=0.82），建议提高权重至 0.28",
    "doc_completeness 相关性低（r=0.20），可能是噪音维度，建议降低权重"
  ]
}

退出码：0=成功，1=参数错误，2=样本不足（< min-samples），输出警告但仍计算
```

### 3.4 gap_analyzer.py

```
用法：
  python3 gap_analyzer.py --specs-dir .specs [--min-samples 3] [--threshold 1.5]

参数：
  --specs-dir    : 项目 spec 根目录（必选）
  --min-samples  : 最小样本数（可选，默认 3）
  --threshold    : 偏差阈值（可选，默认 1.5 分）

输入：
  - .specs/traces.jsonl（含标签的轨迹记录）
  - .specs/LESSONS.md（关联失败经验）
  - .specs/.lessons.jsonl（索引，如存在）

输出（JSON）：
{
  "total_traces": 8,
  "overall_avg_score": 7.2,
  "slices": [
    {
      "dimension": "change_type",
      "slices": [
        {"value": "feature", "count": 4, "avg_score": 7.5, "deviation": +0.3},
        {"value": "bugfix", "count": 2, "avg_score": 6.8, "deviation": -0.4},
        {"value": "refactor", "count": 2, "avg_score": 5.2, "deviation": -2.0, "weak": true}
      ]
    },
    {
      "dimension": "complexity",
      "slices": [
        {"value": "LITE", "count": 3, "avg_score": 8.1, "deviation": +0.9},
        {"value": "STANDARD", "count": 3, "avg_score": 7.0, "deviation": -0.2},
        {"value": "HEAVY", "count": 2, "avg_score": 5.5, "deviation": -1.7, "weak": true}
      ]
    }
  ],
  "weak_slices": [
    {
      "dimension": "change_type",
      "value": "refactor",
      "avg_score": 5.2,
      "deviation": -2.0,
      "related_lessons": ["LESS-003 重构后测试不充分导致回滚"],
      "suggestion": "refactor 类型变更建议增强测试阶段覆盖"
    }
  ]
}

退出码：0=成功，1=参数错误，2=样本不足
```

### 3.5 context_summarizer.py

```
用法：
  python3 context_summarizer.py --stage 3 --specs-dir .specs/<id>
    [--skill-dir <flow-go skill 目录>]

参数：
  --stage       : 目标阶段编号 0-7（必选）
  --specs-dir   : 当前 Change 的 spec 目录（必选）
  --skill-dir   : flow-go skill 根目录（可选，默认从脚本路径推断）

输入：
  - 各阶段上下文需求清单（从对应 stages/*.md 读取）
  - 上游工件文件（REQUIREMENT.md、DESIGN.md 等）

输出（stdout，Markdown 格式）：
  - 按当前阶段的上下文需求清单，仅提取必选字段
  - 关键决策保留原文
  - 描述性内容压缩为一行

示例输出（--stage 3）：
  ## 上下文摘要（3-开发阶段）
  ### REQUIREMENT（必选）
  - 验收准则：AC-1~AC-10（完整保留）
  - 范围排除：5 条（完整保留）
  - 原则：7 条（完整保留）
  ### DESIGN（必选）
  - 架构图：ASCII 图（完整保留）
  - API 设计：5 个脚本接口（完整保留）
  - ADR：6 条决策（标题+决策行，省略背景和理由）
  ### CONTEXT（可选）
  - 域语言：3 条（完整保留）
  - 禁止清单：2 条（完整保留）

退出码：0=成功，1=参数错误，2=上游工件缺失
```

## 4. ADR

### ADR-001 轨迹数据存储格式选 JSONL
- 背景：需要存储每个 Change 的执行轨迹，供后续分析和飞轮巡检消费
- 选项：A) JSONL 文件 / B) SQLite 数据库 / C) 每个 Change 独立 JSON 文件 + 索引
- 决策：A) JSONL 文件
- 理由：与现有 health-history.jsonl 和 strategies.jsonl 格式一致；追加写入无需锁；JSONL 可用 grep/jq/Python 逐行处理；flow-go 单项目数据量有限（通常 < 100 条），JSONL 性能足够；无需引入 SQLite 依赖

### ADR-002 标签维度固定 6 个
- 背景：Gap 分析需要按维度分片统计，维度太多增加分析复杂度，太少定位不准
- 选项：A) 固定 6 维 / B) 用户自定义维度 / C) 动态从数据推断维度
- 决策：A) 固定 6 维（变更类型/复杂度/阶段瓶颈/回溯次数/涉及文件数/是否跨子系统）
- 理由：6 个维度覆盖了影响 flow-go 流程质量的主要因素；固定维度简化脚本实现和结果解读；用户自定义需要额外 UI 增加复杂度；如后续需扩展，修改 gap_analyzer.py 的 TAG_DIMENSIONS 常量即可

### ADR-003 回滚/热修检测基于 .specs 归档记录
- 背景：AC-5 需要检测已归档 Change 是否被后续热修/废弃引用
- 选项：A) 扫描 .specs/archive/ 下的工件 / B) 扫描 git log / C) 要求用户手动标记
- 决策：A) 扫描 .specs/archive/ 下的工件
- 理由：flow-go 以文件驱动，所有流程状态都在 .specs 目录内；git log 包含非 flow-go 管理的变更，噪音大；热修流程必写 CHANGE.md（含关联信息），废弃流程必写 ABANDONED.md，这些都是可检测的信号；手动标记增加人工负担，违反 Principles

### ADR-004 飞轮巡检作为独立流程而非嵌入归档
- 背景：飞轮巡检可以每次归档后自动运行，也可以独立周期性运行
- 选项：A) 嵌入归档流程末尾 / B) 独立流程（手动+周期） / C) 混合：归档后轻量分析 + 周期深度分析
- 决策：B) 独立流程（手动+周期）
- 理由：归档流程的职责是安全归档，不应承担分析任务（单一职责）；飞轮巡检需要读取多个 Change 的轨迹数据，归档时只有一个 Change 的数据；嵌入归档会延长归档时间（违反"不增加人工负担"原则）；独立流程可以灵活选择分析深度和频率

### ADR-005 上下文摘要按阶段定义需求清单
- 背景：各阶段需要从上游工件加载不同字段，全文加载浪费 token
- 选项：A) 每阶段硬编码需求清单在 context_summarizer.py / B) 在阶段指南文件中声明需求清单 / C) 自动分析下游使用情况生成清单
- 决策：B) 在阶段指南文件中声明需求清单
- 理由：阶段指南是流程定义的核心，上下文需求属于流程定义的一部分；在阶段指南中声明可随阶段规则一起维护；硬编码在脚本中会增加脚本与阶段文件的耦合；自动分析需要大量数据支撑（当前无），且结果可能不准确

### ADR-006 跨 Change 顿悟复用 evolution_reflect.py 写入逻辑
- 背景：AC-8 需要跨 Change 聚合顿悟，现有 evolution_reflect.py 已实现单 Change 内顿悟
- 选项：A) 独立实现新顿悟逻辑 / B) 复用 evolution_reflect.py 的写入逻辑，仅扩展数据源 / C) 替换现有顿悟逻辑
- 决策：B) 复用 evolution_reflect.py 的写入逻辑，仅扩展数据源
- 理由：写入 LESSONS.md 的逻辑（格式、索引更新、用户确认流程）已验证可靠；仅数据源不同（单 Change 内 signature vs 跨 Change 归因标签聚合），核心逻辑可复用；避免两套顿悟机制导致 LESSONS.md 格式不一致

## 5. 风险

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| traces.jsonl 积累大量数据后性能下降 | 中 | 中 | JSONL 逐行读取，内存友好；如超 1000 条可考虑归档旧记录到 traces-archive.jsonl |
| 健康评分校准样本不足导致权重偏移 | 高 | 高 | 设置最小样本数阈值（默认 5），不足时仅输出警告不自动调整；权重调整需用户确认 |
| 标签维度不覆盖实际薄弱环节 | 中 | 中 | gap_analyzer.py 的 TAG_DIMENSIONS 为常量定义，修改成本低；定期运行 artifact_format_analyzer.py 可发现新的维度需求 |
| 上下文摘要遗漏关键字段导致下游阶段信息不足 | 中 | 高 | 关键决策字段强制保留原文（不压缩）；摘要生成后由人工确认；优雅降级：如摘要质量不足，可回退到全文加载 |
| outcome 检测不准确（.specs 归档记录不完整） | 中 | 中 | outcome 字段默认 null（未知），不强制填写；检测逻辑为"发现关联则标记"，而非"未发现则标记成功" |
| 飞轮巡检周期触发在不同宿主 agent 间不兼容 | 中 | 低 | 设计为"手动优先、周期可选"；手动触发时功能完整；CronCreate/loop 为增强而非依赖 |

## 6. 既有架构对齐

### 触碰模块
| 模块 | 修改类型 | 说明 |
|------|---------|------|
| `references/scripts/` | 新增 | 5 个新脚本，不修改现有 12 个 |
| `references/stages/*.md` | 修改 | 8 个阶段指南各增加"上下文需求清单"章节 |
| `references/artifacts/meta-artifacts.md` | 修改 | 增加 TRACE.md 和 traces.jsonl 格式定义 |
| `SKILL.md` | 修改 | 第七步状态更新增加轨迹采集触发；新增"飞轮巡检"意图路由；新增配置项 |
| `references/stages/special-flows.md` | 修改 | 归档流程步骤 4.5 后插入轨迹采集步骤 |
| `references/sync-matrix.md` | 修改 | 新增 traces.jsonl 的变更→同步映射 |

### 禁动清单
- **不修改** `complexity_classifier.py`（复杂度分级逻辑独立）
- **不修改** `health_scorer.py` 的评分算法（校准仅输出建议，不自动修改权重）
- **不修改** `evolution_reflect.py` 的核心逻辑（仅扩展数据源接口）
- **不修改** STATE.md 的字段结构（仅更新现有字段的值）
- **不修改** `.claude/settings.local.json` 的权限配置

### 沿用决策
- 脚本接口风格沿用现有模式：argparse CLI + JSON stdout + 退出码语义
- JSONL 格式沿用 health-history.jsonl 的追加写入模式
- 标签索引沿用 lessons_indexer.py 的 JSONL 索引模式
- 交叉评审沿用 cross-review-matrix.md 的子代理调用协议
- 配置读取沿用 `.flowgo-config` 优先级链

## 7. 阶段上下文需求清单定义

### 设计原则
- 每个阶段指南文件末尾增加 `## 上下文需求清单` 章节
- 字段分 **必选**（缺失则无法执行）和 **可选**（有则更好）
- 关键决策字段标记为 **原文保留**（不压缩）
- context_summarizer.py 根据此清单生成摘要

### 各阶段上下文需求

#### 0-需求
| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| — | — | — | — |

#### 1-设计
| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |
| REQUIREMENT.md | 非功能需求 | 必选 | 原文保留 |
| REQUIREMENT.md | Out of Scope | 必选 | 原文保留 |
| REQUIREMENT.md | Principles | 必选 | 原文保留 |
| REQUIREMENT.md | 用户故事 | 可选 | 压缩为一行 |
| CONTEXT.md | 域语言 | 必选 | 原文保留 |
| CONTEXT.md | 已锁决策 | 必选 | 原文保留 |
| CONTEXT.md | 禁止清单 | 必选 | 原文保留 |

#### 2-任务
| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |
| DESIGN.md | 架构图 | 必选 | 原文保留 |
| DESIGN.md | API 设计 | 必选 | 原文保留 |
| DESIGN.md | ADR | 必选 | 标题+决策行 |
| DESIGN.md | 风险 | 可选 | 标题+缓解行 |
| DESIGN.md | 既有架构对齐 | 必选 | 原文保留 |

#### 3-开发
| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |
| REQUIREMENT.md | 范围排除 | 必选 | 原文保留 |
| REQUIREMENT.md | 原则 | 必选 | 原文保留 |
| DESIGN.md | 架构图 | 必选 | 原文保留 |
| DESIGN.md | API 设计 | 必选 | 原文保留 |
| TASK.md | 当前任务 | 必选 | 原文保留 |
| CONTEXT.md | 域语言 | 可选 | 压缩为一行 |
| CONTEXT.md | 禁止清单 | 必选 | 原文保留 |

#### 4-测试
| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |
| TASK.md | 全部任务 | 必选 | 原文保留 |
| SUMMARY.md | 开发摘要 | 必选 | 原文保留 |

#### 5-审查
| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |
| DESIGN.md | 架构图 | 必选 | 原文保留 |
| DESIGN.md | API 设计 | 必选 | 原文保留 |
| DESIGN.md | ADR | 必选 | 标题+决策行 |
| SUMMARY.md | 全部 | 必选 | 原文保留 |
| TEST.md | 全部 | 必选 | 原文保留 |

#### 6-部署
| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REVIEW.md | 全部 | 必选 | 原文保留 |
| CHANGE.md | 验收线 | 必选 | 原文保留 |
| DESIGN.md | 既有架构对齐 | 可选 | 原文保留 |

#### 7-验收
| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |
| CHANGE.md | 验收线 + 范围排除 | 必选 | 原文保留 |
| DEPLOY.md | 全部 | 必选 | 原文保留 |

## 8. 新增配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `flywheel_min_samples` | 3 | 飞轮分析最小轨迹样本数 |
| `flywheel_gap_threshold` | 1.5 | Gap 分析偏差阈值（分） |
| `flywheel_outcome_check` | true | 是否自动检测归档后 outcome |
| `flywheel_outcome_days` | 7 | outcome 自动检测窗口（天） |
| `context_summarize` | false | 是否默认启用上下文摘要（false=全文加载，true=摘要加载） |
| `trace_auto_collect` | true | 归档时是否自动采集轨迹 |

## 9. SKILL.md 修改清单

### 意图路由表新增
| 用户输入特征 | 路由到 | 角色 |
|---|---|---|
| `飞轮巡检` / `飞轮报告` / `周报` | 飞轮巡检流程 | 自动 |
| `标记结果` / `更新 outcome` | outcome 标记流程 | 自动 |
| `轨迹分析` / `gap 分析` | 运行 gap_analyzer.py | 自动 |
| `校准评分` / `校准权重` | 运行 health_calibration.py | 自动 |

### 第七步状态更新新增
归档流程步骤 4.5 后插入：
```
4.5 **轨迹采集**（配置项 `trace_auto_collect` 控制，默认 true）：
   执行 `python3 references/scripts/trace_collector.py --specs-dir .specs/<id> --change-id <id>`
   → 生成 TRACE.md + 追加 traces.jsonl
```

### 进化分析增强
现有自动进化触发逻辑增加：
```
飞轮巡检触发条件（新增）：
- 手动触发：`飞轮巡检` / `飞轮报告` / `周报`
- 周期触发：通过 /loop 7d "运行 flow-go 飞轮巡检"
执行步骤：
1. 运行 gap_analyzer.py → 输出 Gap 报告
2. 运行 health_calibration.py → 输出校准报告（样本充足时）
3. 检查跨 Change 聚合顿悟 → 复用 evolution_reflect.py 写入逻辑
4. 生成 EVOLUTION-WEEKLY-YYYYMMDD.md
5. 顿悟候选请用户确认
```

## 10. 归档流程修改清单

### special-flows.md 归档步骤修改

在步骤 4 和步骤 5 之间插入：
```
4.5 **轨迹采集**（配置项 `trace_auto_collect` 控制，默认 true）：
   - 执行 `python3 references/scripts/trace_collector.py --specs-dir .specs/<id> --change-id <id>`
   - 生成 `.specs/<id>/TRACE.md`
   - 追加记录到 `.specs/traces.jsonl`
   - 采集失败不阻塞归档（输出警告，继续执行）
```

### outcome 自动标记（新增能力）

归档完成后，在下次归档/飞轮巡检/手动标记时执行：
```
1. 读取 traces.jsonl 最近 N 条（outcome == null）的记录
2. 对每条记录，扫描 .specs/archive/ 下是否有 ABANDONED.md 或热修 CHANGE.md 引用该 change-id
3. 有引用 → 更新 outcome 字段（hotfixed/abandoned/degraded）
4. 无引用且超过 outcome_days 天 → 更新 outcome = "success"
5. 写回 traces.jsonl（替换对应行）
```

## 11. 新增工件：TRACE.md

### meta-artifacts.md 新增定义

```markdown
## TRACE.md（.specs/<id>/TRACE.md）

轨迹记录，归档时由 trace_collector.py 自动生成。

### 格式
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
```
