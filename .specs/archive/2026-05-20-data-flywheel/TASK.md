# TASK — data-flywheel

## 批次总览

| 批次 | 优先级 | 任务 | 依赖 |
|------|--------|------|------|
| P0 | Must | T01-T07 | T01+T02→T03→T04(+T07); T05→T06 |
| P1 | Should | T08-T10 | T01 |
| P2 | Could | T11-T13 | T08,T09 |

## 依赖图

```
T01 [P]────┬──→ T03 ──→ T04
           │         ↑
T02 [P]────┤      T07 [P]
           │
T05 [P]────┼──→ T06
           │
           ├──→ T08 [P]
           ├──→ T09 [P]
           └──→ T10 ──→ (outcome 自动标记)

T11 [P]──────→ (独立，无下游依赖)

            T08+T09 ──→ T12 ──→ T13
```

## 并行分组

### 并行组 1（P0 基础，可同时开发）
- T01 trace_collector.py
- T02 meta-artifacts 新增定义
- T05 context_summarizer.py
- T07 SKILL.md 新增配置项

### 串行链 1（依赖并行组 1）
- T03 → T04（归档流程修改 → SKILL.md 路由+状态更新；T04 还依赖 T07 的配置项）

### 串行链 2（依赖并行组 1）
- T06（阶段指南上下文清单，依赖 T05）

### 并行组 2（P1 分析，依赖 T01）
- T08 gap_analyzer.py
- T09 health_calibration.py
- T10 outcome 自动标记

### 串行链 3（P2 自动化）
- T11（独立，无依赖，可随时执行）
- T12 → T13（飞轮流程 → 周报模板；T12 依赖 T08+T09）

---

## T01
- **name**: 创建 trace_collector.py
- **priority**: Must
- **batch**: P0
- **read_files**:
  - references/scripts/health_scorer.py（沿用 CLI 风格）
  - references/scripts/lessons_indexer.py（沿用 JSONL 索引模式）
- **write_files**:
  - references/scripts/trace_collector.py
- **action**: 创建轨迹采集脚本。实现 argparse CLI，接受 --specs-dir / --change-id / --health-score / --complexity / --path-mode / --tags / --output-trace / --output-jsonl 参数。读取 STATE.md 获取阶段信息，扫描 .specs/<id>/ 下工件提取关键决策（从 REVIEW.md 提取评审轮次，从各工件 frontmatter 提取阶段标记），读取 health-history.jsonl 获取最近评分，生成 TRACE.md（人类可读）和 traces.jsonl 记录（机器可读）。traces.jsonl 记录格式严格遵循 DESIGN.md 第 3.1 节定义。退出码 0=成功/1=参数错误/2=工件缺失
- **verify**: `python3 references/scripts/trace_collector.py --help 2>&1 | grep -q "trace_collector"`
- **done**: trace_collector.py 可执行，--help 输出包含所有参数说明，traces.jsonl 记录格式与 DESIGN.md 定义一致
- **depends_on**: 无
- **context_budget**: small
- **agent_hint**: 参照 health_scorer.py 的 CLI 风格（argparse + JSON stdout + 退出码）

## T02
- **name**: meta-artifacts.md 新增 TRACE.md 和 traces.jsonl 定义
- **priority**: Must
- **batch**: P0
- **read_files**:
  - references/artifacts/meta-artifacts.md
  - .specs/data-flywheel/DESIGN.md（第 11 节 TRACE.md 格式）
- **write_files**:
  - references/artifacts/meta-artifacts.md
- **action**: 在 meta-artifacts.md 末尾追加 TRACE.md 工件定义章节（格式按 DESIGN.md 第 11 节）和 traces.jsonl 数据格式定义。包含完整性校验清单项（grep 用于闸门检查）
- **verify**: `grep -c "TRACE.md" references/artifacts/meta-artifacts.md`
- **done**: meta-artifacts.md 包含 TRACE.md 工件格式定义和 traces.jsonl 数据格式定义
- **depends_on**: 无
- **context_budget**: small
- **agent_hint**: 参照 meta-artifacts.md 中 STATE.md/LESSONS.md 的定义风格

## T03
- **name**: 归档流程新增轨迹采集步骤
- **priority**: Must
- **batch**: P0
- **read_files**:
  - references/stages/special-flows.md
  - references/scripts/trace_collector.py（T01 产出）
- **write_files**:
  - references/stages/special-flows.md
- **action**: 在归档流程步骤 4 和步骤 5 之间插入步骤 4.5（轨迹采集）。内容：执行 trace_collector.py，生成 TRACE.md 和追加 traces.jsonl，采集失败不阻塞归档（输出警告继续执行）。在归档自检清单中新增一项。在废弃流程中也增加 outcome 标记相关说明
- **verify**: `grep -c "trace_collector" references/stages/special-flows.md`
- **done**: 归档流程包含步骤 4.5 轨迹采集，自检清单已更新
- **depends_on**: T01, T02
- **context_budget**: small
- **agent_hint**: 参照归档流程现有步骤的格式风格

## T04
- **name**: SKILL.md 新增路由 + 状态更新增强
- **priority**: Must
- **batch**: P0
- **read_files**:
  - SKILL.md
  - .specs/data-flywheel/DESIGN.md（第 9 节修改清单）
- **write_files**:
  - SKILL.md
- **action**: 1) 意图路由表新增 4 条：飞轮巡检/标记结果/轨迹分析/校准评分。2) 第七步状态更新中归档流程后插入轨迹采集触发（引用配置项 trace_auto_collect，由 T07 写入）。3) 进化分析增强：新增飞轮巡检触发条件和执行步骤
- **verify**: `grep -c "flywheel" SKILL.md`
- **done**: SKILL.md 包含 4 条新路由、轨迹采集触发、飞轮巡检流程
- **depends_on**: T03, T07
- **context_budget**: medium
- **agent_hint**: 修改 SKILL.md 时严格保持现有格式和缩进，新增路由插入在废弃路由之后

## T05
- **name**: 创建 context_summarizer.py
- **priority**: Must
- **batch**: P0
- **read_files**:
  - references/scripts/health_scorer.py（沿用 CLI 风格）
  - references/stages/3-develop.md（理解下游需求）
- **write_files**:
  - references/scripts/context_summarizer.py
- **action**: 创建上下文摘要生成脚本。实现 argparse CLI，接受 --stage / --specs-dir / --skill-dir 参数。从对应 stages/<N>-<name>.md 中读取「上下文需求清单」章节，按清单从上游工件提取必选字段，关键决策保留原文，描述性内容压缩为一行。输出 Markdown 格式到 stdout。stage 指南无需求清单时输出全文（优雅降级）。退出码 0=成功/1=参数错误/2=上游工件缺失
- **verify**: `python3 references/scripts/context_summarizer.py --help 2>&1 | grep -q "context_summarizer"`
- **done**: context_summarizer.py 可执行，--help 包含所有参数，输出格式为 Markdown 摘要
- **depends_on**: 无
- **context_budget**: small
- **agent_hint**: 参照 health_scorer.py 的 CLI 风格。核心逻辑：读取阶段文件 → 解析需求清单 → 按清单提取工件字段 → 输出摘要

## T06
- **name**: 8 个阶段指南新增上下文需求清单
- **priority**: Must
- **batch**: P0
- **read_files**:
  - references/stages/0-requirement.md
  - references/stages/1-design.md
  - references/stages/2-task.md
  - references/stages/3-develop.md
  - references/stages/4-test.md
  - references/stages/5-review.md
  - references/stages/6-deploy.md
  - references/stages/7-acceptance.md
  - .specs/data-flywheel/DESIGN.md（第 7 节各阶段清单）
- **write_files**:
  - references/stages/0-requirement.md
  - references/stages/1-design.md
  - references/stages/2-task.md
  - references/stages/3-develop.md
  - references/stages/4-test.md
  - references/stages/5-review.md
  - references/stages/6-deploy.md
  - references/stages/7-acceptance.md
- **action**: 在每个阶段指南文件末尾追加「## 上下文需求清单」章节，内容严格按 DESIGN.md 第 7 节定义。格式为表格（来源工件/字段/必选或可选/保留方式）。0-需求阶段无上游，清单为空但写明"首个阶段，无上游依赖"
- **verify**: `grep -l "上下文需求清单" references/stages/*.md | wc -l`
- **done**: 8 个阶段指南文件均包含「上下文需求清单」章节，内容与 DESIGN.md 定义一致
- **depends_on**: T05
- **context_budget**: medium
- **agent_hint**: 每个 stage 文件追加 ~10 行，保持格式统一。使用 DESIGN.md 第 7 节的表格内容

## T07
- **name**: SKILL.md 新增配置项
- **priority**: Must
- **batch**: P0
- **read_files**:
  - SKILL.md
  - .specs/data-flywheel/DESIGN.md（第 8 节配置项）
- **write_files**:
  - SKILL.md
- **action**: 在 SKILL.md 配置表中新增 6 个配置项：flywheel_min_samples(3)/flywheel_gap_threshold(1.5)/flywheel_outcome_check(true)/flywheel_outcome_days(7)/context_summarize(false)/trace_auto_collect(true)。同时在配置格式示例中补充新配置项
- **verify**: `grep -c "flywheel_min_samples" SKILL.md`
- **done**: SKILL.md 配置表包含 6 个新配置项，默认值与 DESIGN.md 一致
- **depends_on**: 无
- **context_budget**: small
- **agent_hint**: 在现有配置表末尾追加，保持表格格式一致。同时更新 YAML 示例

## T08
- **name**: 创建 gap_analyzer.py
- **priority**: Should
- **batch**: P1
- **read_files**:
  - references/scripts/health_scorer.py（沿用 CLI 风格）
  - .specs/data-flywheel/DESIGN.md（第 3.4 节接口定义）
- **write_files**:
  - references/scripts/gap_analyzer.py
- **action**: 创建 Gap 分析脚本。实现 argparse CLI，接受 --specs-dir / --min-samples / --threshold 参数。读取 traces.jsonl，按 6 个固定维度（TAG_DIMENSIONS 常量定义）分片统计平均健康评分，识别偏差 > threshold 的切片为 weak，读取 LESSONS.md 和 .lessons.jsonl 关联失败经验。输出 JSON 报告到 stdout。样本不足时输出警告退出码 2。退出码 0=成功/1=参数错误/2=样本不足
- **verify**: `python3 references/scripts/gap_analyzer.py --help 2>&1 | grep -q "gap_analyzer"`
- **done**: gap_analyzer.py 可执行，--help 包含所有参数，JSON 输出包含 slices/weak_slices/related_lessons
- **depends_on**: T01
- **context_budget**: small
- **agent_hint**: 参照 health_scorer.py 的 CLI 风格。核心：JSONL 逐行读取 → 按 6 维分片 → statistics.mean 计算各片平均 → 偏差识别

## T09
- **name**: 创建 health_calibration.py
- **priority**: Should
- **batch**: P1
- **read_files**:
  - references/scripts/health_scorer.py（沿用权重定义）
  - .specs/data-flywheel/DESIGN.md（第 3.3 节接口定义）
- **write_files**:
  - references/scripts/health_calibration.py
- **action**: 创建健康评分校准脚本。实现 argparse CLI，接受 --specs-dir / --min-samples 参数。读取 traces.jsonl 中 outcome != null 的记录，提取 health_dimensions 和 outcome，用 statistics 模块计算各维度与 outcome 的 Spearman 相关性（用排名代替精确相关系数），对比当前权重与相关性建议权重。输出 JSON 校准报告。样本不足时输出警告退出码 2。退出码 0=成功/1=参数错误/2=样本不足
- **verify**: `python3 references/scripts/health_calibration.py --help 2>&1 | grep -q "health_calibration"`
- **done**: health_calibration.py 可执行，--help 包含所有参数，JSON 输出包含 correlations/suggestions
- **depends_on**: T01
- **context_budget**: small
- **agent_hint**: 参照 health_scorer.py 的权重常量 DIMENSIONS。相关性计算用 statistics 模块，无需 numpy

## T10
- **name**: outcome 自动标记逻辑
- **priority**: Should
- **batch**: P1
- **read_files**:
  - references/scripts/trace_collector.py（T01 产出，扩展功能）
  - references/stages/special-flows.md（理解归档/废弃/热修流程）
- **write_files**:
  - references/scripts/trace_collector.py（新增 --check-outcome 模式）
- **action**: 在 trace_collector.py 中新增 --check-outcome 模式。执行时：读取 traces.jsonl 中 outcome == null 的记录，对每条扫描 .specs/archive/ 下是否有 ABANDONED.md 或热修 CHANGE.md 引用该 change-id。有引用 → 更新 outcome 为 hotfixed/abandoned/degraded。无引用且超过 outcome_days 天 → 更新为 success。写回 traces.jsonl（原地替换对应行）
- **verify**: `python3 references/scripts/trace_collector.py --help 2>&1 | grep -q "check-outcome"`
- **done**: trace_collector.py 支持 --check-outcome 模式，可自动检测并更新 outcome 字段
- **depends_on**: T01
- **context_budget**: small
- **agent_hint**: 扩展现有 trace_collector.py，不新建脚本。--check-outcome 与常规采集模式互斥（argparse 互斥组）

## T11
- **name**: 创建 artifact_format_analyzer.py
- **priority**: Could
- **batch**: P2
- **read_files**:
  - references/artifacts/spec-artifacts.md
  - references/artifacts/task-artifacts.md
  - references/artifacts/quality-artifacts.md
  - references/artifacts/deploy-artifacts.md
  - references/artifacts/meta-artifacts.md
  - references/stages/*.md（交叉引用字段使用）
- **write_files**:
  - references/scripts/artifact_format_analyzer.py
- **action**: 创建工件格式分析脚本。实现 argparse CLI，接受 --skill-dir / --format 参数。读取 artifacts/*.md 解析模板中的字段定义（markdown 表格和章节标题），读取 stages/*.md 搜索字段引用，交叉对比找出"模板定义但下游未引用"的字段。统计 token 效率（信息行数/总行数）。输出 JSON 报告到 stdout。退出码 0=成功/1=参数错误
- **verify**: `python3 references/scripts/artifact_format_analyzer.py --help 2>&1 | grep -q "artifact_format_analyzer"`
- **done**: artifact_format_analyzer.py 可执行，JSON 输出包含 templates/summary/suggestions
- **depends_on**: 无
- **context_budget**: medium
- **agent_hint**: 核心逻辑：解析 markdown 模板（grep 表格行）→ 在阶段文件中搜索字段名 → 计算覆盖率。无需精确 NLP，用字符串匹配即可

## T12
- **name**: SKILL.md 新增飞轮巡检流程
- **priority**: Could
- **batch**: P2
- **read_files**:
  - SKILL.md
  - .specs/data-flywheel/DESIGN.md（第 9 节飞轮巡检流程）
  - references/sync-matrix.md
- **write_files**:
  - SKILL.md
  - references/sync-matrix.md
- **action**: 在 SKILL.md 进化分析部分增强飞轮巡检流程。增加：1) 手动触发路由的完整执行步骤（运行 gap_analyzer → health_calibration → 检查顿悟 → 生成周报）。2) EVOLUTION-WEEKLY 模板引用。3) sync-matrix.md 新增 traces.jsonl 的变更→同步映射
- **verify**: `grep -c "EVOLUTION-WEEKLY" SKILL.md`
- **done**: SKILL.md 包含完整飞轮巡检流程，sync-matrix.md 已更新
- **depends_on**: T08, T09
- **context_budget**: small
- **agent_hint**: 参照现有进化分析的格式风格。飞轮巡检作为进化分析的增强而非替代

## T13
- **name**: meta-artifacts.md 新增 EVOLUTION-WEEKLY 模板
- **priority**: Could
- **batch**: P2
- **read_files**:
  - references/artifacts/meta-artifacts.md
  - .specs/data-flywheel/DESIGN.md（飞轮周报需求）
- **write_files**:
  - references/artifacts/meta-artifacts.md
- **action**: 在 meta-artifacts.md 末尾追加 EVOLUTION-WEEKLY-YYYYMMDD.md 工件模板。格式包含：报告周期/归档数量/健康评分趋势（表格）/Top-3 薄弱切片/新增 LESSONS 候选/策略捕获记录/下一步建议
- **verify**: `grep -c "EVOLUTION-WEEKLY" references/artifacts/meta-artifacts.md`
- **done**: meta-artifacts.md 包含 EVOLUTION-WEEKLY 模板定义
- **depends_on**: T12
- **context_budget**: small
- **agent_hint**: 参照 meta-artifacts.md 中现有模板的格式风格
