# CHANGE — evolution-pipeline-p0

## Why（为什么做）
借鉴 Skill Evolver（张思宇）的 8 阶段 Loop + 3 层评测 + 5 维 AND 门控思想，以及 Karpathy autoresearch 的迭代骨架，发现 flow-go 现有进化体系存在三个核心差距：
1. Trace 采集后未回馈诊断（闭环断裂）
2. 门控仅检查文件存在性（质量深度不足）
3. 结果日志缺少实验记录（数据基础薄弱）

这三个差距导致进化信号提取依赖正则匹配而非结构化数据，门控无法判断工件质量，实验记录无法支撑趋势分析。

## What（做什么）
三项核心优化：
1. **Trace 诊断闭环**：改造 `evolution_signal.py`，优先从 `traces.jsonl` 读取结构化数据（闸门阻断次数、阶段瓶颈、健康评分趋势），正则匹配降级为补充；新增 `gate_blocks > 0` 强信号维度
2. **AND 门控增强**：改造 `gate_check.py`，新增 `--mode quality-gate` 模式，增加质量/回归/安全/范围四个检查维度，AND 逻辑（任一不过即失败）
3. **结果日志标准化**：改造 `health-history.jsonl` 格式，新增 `changes_made`、`trigger`、`previous_score` 字段，为进化分析提供完整实验上下文

## 影响面
- 涉及模块：references/scripts/evolution_signal.py, references/scripts/gate_check.py, references/scripts/trace_collector.py, references/scripts/health_scorer.py
- 数据库变更：否
- API 变更：否（均为 CLI 脚本）
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- 不实现三层评测体系（P1）
- 不实现 GT 测试用例（P1）
- 不实现半主动进化循环（P2）
- 不引入新的外部依赖
- 不修改 flow-go SKILL.md 主文件（阶段定义不变）

## 验收线
三项优化全部实现，脚本可通过命令行调用且输出符合预期格式，现有归档数据向前兼容。

## 路径建议
增量，理由：改动集中在 4 个 Python 脚本，不涉及阶段流程变更，不触碰 SKILL.md 主文件。每个脚本的改动独立，可逐个验证。
