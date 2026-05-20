# DESIGN — evolution-pipeline-p0

## 技术栈

沿用现有 Python 3 + argparse + stdlib。不引入外部依赖。

选择理由：REQUIREMENT.md Principles 要求"不引入新的外部依赖"且"与现有 scripts/ 目录风格一致"。

## 架构图

```
                         traces.jsonl
                              │
                              ▼
  ┌──────────────────────────────────────────────────┐
  │              evolution_signal.py                  │
  │  ┌──────────────┐    ┌───────────────────────┐  │
  │  │ Trace 读取器  │───▶│ 信号提取（优先 trace） │  │
  │  │ (--traces)   │    │ ↓ fallback 正则匹配    │  │
  │  └──────────────┘    └───────────────────────┘  │
  └──────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────┐
  │                gate_check.py                      │
  │  ┌──────────┐                                     │
  │  │ 工件检查  │  (现有功能，不变)                    │
  │  └──────────┘                                     │
  │  ┌────────────────────────────────────────────┐  │
  │  │ quality-gate (--mode quality-gate)  AND 逻辑│  │
  │  │  ┌─────────┐ ┌──────┐ ┌──────┐ ┌───────┐ │  │
  │  │  │ 质量维度 │ │范围  │ │安全  │ │回归   │ │  │
  │  │  │SUMMARY  │ │git   │ │pattern│ │TEST   │ │  │
  │  │  │verify%  │ │diff  │ │scan  │ │delta  │ │  │
  │  │  └─────────┘ └──────┘ └──────┘ └───────┘ │  │
  │  └────────────────────────────────────────────┘  │
  └──────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────────────┐
  │              health_scorer.py                     │
  │  现有: 7维评分 → health-history.jsonl             │
  │  新增: +changes_made +trigger +previous_score     │
  │        ↓                                         │
  │  health-history.jsonl (增强格式)                   │
  └──────────────────────────────────────────────────┘
```

数据流向：
1. `trace_collector.py` 采集 → `traces.jsonl`（现有，不改）
2. `evolution_signal.py --traces` 消费 `traces.jsonl` → 结构化信号（新增）
3. `gate_check.py --mode quality-gate` 独立运行 4 维 AND 检查（新增）
4. `health_scorer.py` 追加增强格式到 `health-history.jsonl`（改格式）

模块间关系：4 个脚本通过 JSONL 文件松耦合，无直接 import 依赖。

## API 设计

### evolution_signal.py — 新增参数

```
现有（不变）：python3 evolution_signal.py --specs-dir .specs/<id>
新增：       python3 evolution_signal.py --specs-dir .specs/<id> --traces .specs/traces.jsonl
```

| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `--specs-dir` | path | 是 | 现有，不变 |
| `--output` | path | 否 | 现有，不变 |
| `--traces` | path | 否，新增 | traces.jsonl 路径 |

行为：
- 不带 `--traces`：现有正则匹配，不变
- 带 `--traces`：优先从 traces.jsonl 读取 `gate_blocks > 0` 作为强信号，正则匹配降级为补充

新增信号类型：

```json
{
  "type": "gate_blocked_trace",
  "level": "strong",
  "description": "Trace 记录显示闸门被阻断",
  "evidence": ["阶段 3 阻断 2 次", "阶段 5 阻断 1 次"],
  "source": "trace"
}
```

信号去重：trace 产出 `source: "trace"`，正则产出保持原值（信号类型名）。

### gate_check.py — 新增 quality-gate 模式

```
现有（不变）：python3 gate_check.py --stage <N> --specs-dir <path>
现有（不变）：python3 gate_check.py --mode blast-radius --project-dir <path>
新增：       python3 gate_check.py --mode quality-gate --stage <N> --specs-dir <path> --project-dir <path>
```

| 参数 | 类型 | 说明 |
|------|------|------|
| `--mode` | choices | 现有 `blast-radius`，新增 `quality-gate` |
| `--stage` | int | quality-gate 必选 |
| `--specs-dir` | path | quality-gate 必选 |
| `--project-dir` | path | 新增：范围维度需要项目根路径 |

输出格式：

```json
{
  "mode": "quality-gate",
  "passed": false,
  "logic": "AND",
  "dimensions": {
    "quality": { "passed": true, "detail": "...", "source": "SUMMARY.md" },
    "scope": { "passed": true, "detail": "...", "source": "git diff + TASK.md" },
    "security": { "passed": true, "detail": "...", "source": "artifact scan" },
    "regression": { "passed": false, "detail": "...", "source": "TEST.md" }
  }
}
```

4 维检查逻辑：

| 维度 | 输入源 | PASS | FAIL |
|------|--------|------|------|
| quality | SUMMARY.md verify 通过率 | ≥80% 或无 verify 信息 | <80% |
| scope | `git diff --name-only` vs TASK.md 文件列表 | 均在规划内或 TASK.md 无列表 | 有文件超规划 |
| security | specs 下非 TEST.md 工件 | 无危险模式 | 检出危险模式 |
| regression | TEST.md | 无"原已通过用例失败" | 有此类记录 |

AND 逻辑：`passed = quality AND scope AND security AND regression`

### health_scorer.py — 输出格式增强

调用方式不变。health-history.jsonl 新增字段：

| 字段 | 类型 | 来源 |
|------|------|------|
| `changes_made` | `list[str]` | 输入 JSON `files_changed`，默认 `[]` |
| `trigger` | `str` | 输入 JSON `trigger`，默认 `"manual"` |
| `previous_score` | `float \| null` | 自动从 health-history.jsonl 最近一条读取 |

向前兼容：读取旧记录时缺失字段用 `null`/`[]` 填充，不报错。

### trace_collector.py — 无变更

现有 traces.jsonl 格式已满足 evolution_signal.py 新增消费需求。

## ADR

### ADR-1：traces.jsonl 优先，正则匹配降级为补充

- 背景：现有信号提取依赖正则匹配，准确性受文本格式变化影响
- 选项：A 仅用 trace（旧数据无信号）/ B trace 优先 + 正则 fallback / C 并行取并集
- 决策：B
- 理由：兼容旧数据且提升新数据质量。信号去重通过 source 字段区分

### ADR-2：quality-gate AND 逻辑

- 背景：多维度质量把关，加权求和允许高维补偿低维
- 选项：A 加权求和 / B AND 逻辑 / C AND + 告警线
- 决策：B
- 理由：质量把关场景下短板不可补偿

### ADR-3：新字段默认值填充旧记录

- 背景：存量记录无新字段
- 选项：A 迁移脚本 / B 读取时默认值
- 决策：B
- 理由：零运维，应用层容错。默认值：`changes_made=[]`，`trigger=null`，`previous_score=null`

### ADR-4：security 维度固定模式列表

- 背景：需检测危险模式，不能引入外部依赖
- 选项：A semgrep/bandit / B 固定关键词匹配
- 决策：B
- 理由：扫描对象是 spec 文件（非源码），固定模式足够。模式：`BEGIN PRIVATE KEY`、`BEGIN RSA PRIVATE KEY`、`rm -rf /`、`DROP TABLE`、`password\s*=\s*['"]`

## 风险清单

| # | 风险 | 概率 | 影响 | 缓解 |
|---|------|------|------|------|
| R1 | traces.jsonl 路径错误或文件损坏 | 中 | 中 | `--traces` 读取失败时 fallback 正则匹配，不中断 |
| R2 | SUMMARY.md verify 格式不统一 | 中 | 中 | 支持 3 种格式（百分比/分数/关键词）；无法解析时不阻塞 |
| R3 | TASK.md 无文件列表 | 低 | 低 | scope 维度返回 PASS + 标注"跳过" |
| R4 | health-history.jsonl 并发写入 | 低 | 高 | 单进程追加模式，无需改动 |
| R5 | security 扫描误报（测试用例含危险字符串） | 中 | 低 | 扫描范围排除 TEST.md |

## 既有架构对齐

| 检查项 | 结果 |
|--------|------|
| 触碰模块 | `evolution_signal.py` / `gate_check.py` / `health_scorer.py` |
| 禁动清单 | 现有 `check_artifacts()` / `check_blast_radius()` / `detect()` / `compute()` 函数签名和返回格式不变 |
| 沿用决策 | argparse CLI / JSON stdout / stderr 日志 / `--specs-dir` 命名 / JSONL 追加写入 / `_read_file()` 模式 |
| 风格对齐 | 模块级常量 → 辅助函数 → 核心函数 → main() → `if __name__`；`ensure_ascii=False` + `indent=2` |
