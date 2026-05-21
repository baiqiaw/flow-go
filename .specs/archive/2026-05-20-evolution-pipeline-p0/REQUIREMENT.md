# REQUIREMENT — evolution-pipeline-p0

## 用户故事
作为 flow-go 的维护者，我希望进化体系的数据管道完整打通（Trace → 诊断 → 门控 → 日志），以便归档后的进化分析能基于结构化数据而非正则匹配，门控能判断工件质量而非仅检查文件存在。

## 验收准则（BDD）

### AC-1 Trace 诊断闭环
**Given** `traces.jsonl` 中存在某个 change 的完整轨迹记录（含 gate_blocks、health_score、decisions）
**When** 运行 `python3 evolution_signal.py --specs-dir .specs/<id> --traces .specs/traces.jsonl`
**Then** 信号提取优先从 traces.jsonl 读取 gate_blocks > 0 作为强信号，正则匹配作为补充，且输出信号报告包含 `source: "trace"` 标记

### AC-2 gate_blocks 强信号
**Given** traces.jsonl 中某条记录的 `gate_blocks` 任一阶段值 > 0
**When** 运行 evolution_signal.py（含 --traces 参数）
**Then** 生成一个 `type: "gate_blocked_trace"` 的强信号，证据引用具体的阶段和阻断次数

### AC-3 AND 门控增强 — 质量维度
**Given** specs 目录下存在 SUMMARY.md 且包含 verify 通过率信息
**When** 运行 `python3 gate_check.py --mode quality-gate --stage 4 --specs-dir .specs/<id>`
**Then** 质量维度检查 SUMMARY.md 中 verify 通过率，≥80% 为 PASS，<80% 为 FAIL

### AC-4 AND 门控增强 — 范围维度
**Given** 项目根目录存在 git 仓库，且 TASK.md 中标注了预期改动文件列表
**When** 运行 gate_check.py --mode quality-gate
**Then** 范围维度检查 git diff --name-only 改动文件是否超出 TASK.md 规划，未超出为 PASS

### AC-5 AND 门控增强 — 安全维度
**Given** specs 目录下存在工件文件
**When** 运行 gate_check.py --mode quality-gate
**Then** 安全维度扫描工件中的危险模式（硬编码密钥、危险删除命令），未检出为 PASS

### AC-6 AND 门控增强 — 回归维度
**Given** specs 目录下存在 TEST.md 且包含上一轮测试通过记录
**When** 运行 gate_check.py --mode quality-gate
**Then** 回归维度检查 TEST.md 中是否有"原已通过用例失败"的记录，无失败为 PASS

### AC-7 AND 逻辑
**Given** quality-gate 模式下运行所有 4 个维度检查
**When** 任一维度 FAIL
**Then** 总体 gate 结果为 FAIL（AND 逻辑，不可用其他维度的高分补偿）

### AC-8 结果日志增强
**Given** health_scorer.py 计算完健康评分
**When** 评分结果追加到 health-history.jsonl
**Then** 每条记录包含 `changes_made`（改动文件列表）、`trigger`（评分触发原因）、`previous_score`（上次评分）三个新字段

### AC-9 向前兼容
**Given** 旧格式的 health-history.jsonl 记录（无 changes_made/trigger/previous_score 字段）
**When** health_scorer.py 或 evolution_signal.py 读取旧记录
**Then** 不报错，缺失字段用默认值（null/空列表）填充

## 非功能需求
- 性能：quality-gate 全维度检查 < 10 秒（纯文本扫描 + git diff）
- 安全：不引入新的外部依赖
- 兼容：旧格式 health-history.jsonl 向前兼容；旧调用方式（不含 --traces / --mode quality-gate）仍正常工作

## Out of Scope（范围排除）
- 不实现三层评测体系（L1/L2/L3 分层）
- 不实现 GT 测试用例
- 不实现半主动进化循环
- 不修改 flow-go SKILL.md 主文件
- 不修改 stage 文件

## Principles（设计约束原则）
- 所有新代码与现有 scripts/ 目录风格一致（argparse CLI、JSON I/O、UTF-8 编码）
- 不引入新的外部依赖
- 向前兼容：旧格式数据必须可读取，旧调用方式必须正常工作
- 渐进增强：新功能通过新参数（--traces / --mode quality-gate）激活，不影响现有行为

## Key Decisions（关键决策记录）
| 决策 | 理由 | 影响 |
|------|------|------|
| Trace 数据源优先于正则匹配 | Skill Evolver 的 Meta-Harness 研究表明完整 trace 比摘要效果好 44% | evolution_signal.py 需新增 --traces 参数 |
| AND 逻辑而非加权求和 | 加权求和允许一个维度高分补偿另一维度低分，不符合质量把关需求 | gate_check.py quality-gate 模式全维度 AND |
| 新字段用默认值填充旧记录 | 避免迁移脚本，保持向前兼容 | health_scorer.py 读取时需处理缺失字段 |

## 术语表
| 术语 | 含义 |
|------|------|
| Trace 闭环 | trace_collector 采集的数据 → evolution_signal 消费 → 驱动诊断 |
| AND 门控 | 所有检查维度必须全部通过，任一失败即整体失败 |
| quality-gate | gate_check.py 的新模式，检查工件质量而非仅文件存在性 |
| traces.jsonl | trace_collector.py 产出的结构化轨迹日志 |
| health-history.jsonl | health_scorer.py 产出的健康评分历史日志 |
