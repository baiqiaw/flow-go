# REQUIREMENT — data-flywheel

## 用户故事
作为 flow-go 使用者，我希望 flow-go 能自动采集执行数据并形成闭环反馈，以便项目流程越用越精准、工件模板越用越高效，而不是每次都从零开始。

## 验收准则（BDD）

### AC-1 执行轨迹自动采集
**Given**: 一个 Change 完成归档流程
**When**: 归档步骤执行时
**Then**: 自动在 `.specs/<id>/` 下生成 `TRACE.md`，包含：阶段流转路径、每阶段的关键决策摘要、闸门通过次数、健康评分、用户手动干预次数；同时追加一条记录到 `.specs/traces.jsonl`

### AC-2 轨迹数据可用于趋势分析
**Given**: 已有 ≥5 个归档 Change 的 traces.jsonl 记录
**When**: 运行 Gap 分析或飞轮巡检时
**Then**: 能按时间线读取全部轨迹，统计平均健康评分趋势、阶段瓶颈分布、路径模式分布

### AC-3 工件格式 token 效率分析
**Given**: 项目中存在工件模板文件（spec-artifacts.md、task-artifacts.md 等）
**When**: 运行 `artifact_format_analyzer.py` 时
**Then**: 输出各工件模板的 token 效率报告，包含：信息量/总 token 比、冗余格式列表、"模板要求但下游未使用"的字段列表、优化建议

### AC-4 健康评分与实际结果关联
**Given**: 已有 ≥5 个归档 Change 的健康评分和实际结果标签（成功/部分成功/需热修）
**When**: 运行 `health_calibration.py` 时
**Then**: 输出各维度评分与实际结果的相关性分析，给出权重调整建议

### AC-5 归档后实际结果自动标记
**Given**: 一个 Change 完成归档
**When**: 归档后的 7 天内项目继续开发，且下次触发归档/飞轮巡检/手动标记时
**Then**: 系统通过扫描 `.specs/archive/` 下的 ABANDONED.md 记录和热修流程工件（而非 git 历史），检查最近归档的 Change 是否被后续热修/废弃引用，自动更新其 traces.jsonl 记录的 `outcome` 字段（success/degraded/hotfixed/abandoned）

### AC-6 多维标签分片 Gap 定位
**Given**: 已有 ≥3 个归档 Change 的轨迹记录（含标签）
**When**: 运行 `gap_analyzer.py` 时
**Then**: 按 6 个固定维度分片统计平均健康评分，识别显著低于总平均（偏差 > 1.5 分）的切片，关联对应的 LESSONS 条目。6 个维度为：①变更类型（feature/bugfix/refactor/docs/config/chore）②复杂度（LITE/STANDARD/HEAVY）③阶段瓶颈（闸门被阻断次数最多的阶段）④回溯次数（0/1/2/3+）⑤涉及文件数（1-3/4-10/10+）⑥是否跨子系统（是/否）

### AC-7 飞轮周报自动生成
**Given**: 已有 ≥3 个归档 Change 的轨迹记录
**When**: 触发飞轮巡检时（手动或周期）
**Then**: 自动生成 `EVOLUTION-WEEKLY-YYYYMMDD.md`，包含：本周归档数量、健康评分趋势、Top-3 薄弱切片、新增 LESSONS 候选、策略捕获记录

### AC-8 跨 Change 聚合顿悟信号
**Given**: 飞轮巡检发现同一根因（按归因标签聚合）在最近 5 个 Change 的轨迹中出现 ≥3 次
**When**: 跨 Change 聚合顿悟条件满足（区别于现有 evolution_reflect.py 的单 Change 内 signature-based 顿悟）
**Then**: 输出顿悟提示并请用户确认，确认后自动写入 LESSONS.md（复用现有 evolution_reflect.py 的顿悟写入逻辑，仅扩展数据源为跨 Change 聚合）

### AC-9 各阶段上下文需求清单
**Given**: 8 个阶段指南文件（stages/0~7）
**When**: 查看任一阶段指南时
**Then**: 该阶段包含明确的「上下文需求清单」，列出本阶段需要加载的上游工件及其必选/可选字段

### AC-10 阶段摘要生成
**Given**: 上游阶段已产出工件（如 REQUIREMENT.md、DESIGN.md）
**When**: 进入下游阶段（如 3-开发）时
**Then**: 可调用 `context_summarizer.py` 生成本阶段所需的上下文摘要，仅保留必选字段，关键决策保留原文

## 非功能需求
- 性能：新增脚本执行时间 < 5 秒（与现有脚本一致）
- 安全：traces.jsonl 不记录代码内容，仅记录元数据
- 兼容：新脚本仅使用 Python 标准库（与现有 12 个脚本一致）
- 向后兼容：已有项目无 traces.jsonl 时，新脚本优雅降级（输出提示而非报错）

## Out of Scope（范围排除）
- LLM fine-tuning（flow-go 是 prompt 驱动系统）
- 第三方依赖引入
- 跨项目数据共享或集中式数据平台
- 现有脚本的接口签名修改
- 状态机架构重构

## Principles（设计约束原则）
- 所有新脚本必须与现有 scripts/ 目录风格一致（argparse CLI + JSON 输出）
- traces.jsonl 仅追加不删除（审计友好）
- 所有新配置项必须有合理默认值（零配置可运行）
- 上游工件缺失时优雅降级，不阻塞主流程
- 数据采集不可增加阶段执行的人工负担（全自动或半自动）
- 回滚/热修检测基于 .specs 目录内的归档记录而非 git 历史
- 飞轮周期触发依赖宿主 agent 的定时任务能力（如 CronCreate/loop），无此能力时仅支持手动触发（优雅降级）

## Key Decisions（关键决策记录）
| 决策 | 理由 | 影响 |
|------|------|------|
| 单个大型 change 分 3 批实施 | 6 项优化共享 traces.jsonl 数据管线，拆分会重复基础设施 | 开发阶段需按 P0→P1→P2 顺序执行 |
| 轨迹数据存 JSONL 而非 SQLite | 与现有 health-history.jsonl 格式一致，无需额外依赖 | 大数据量时性能不如数据库，但 flow-go 单项目数据量有限 |
| 标签维度固定 6 个 | 覆盖变更类型/复杂度/瓶颈/回溯/文件数/跨系统，足够定位 gap | 后续如需扩展需修改脚本 |
| 上下文摘要按阶段定义需求清单 | 比全文加载更精准，比全量摘要更轻量 | 需修改 8 个阶段指南文件 |
| 飞轮巡检支持手动和周期两种触发 | 手动灵活，周期自动，适应不同使用频率 | 需集成 CronCreate 或 /loop |

## 术语表
| 术语 | 含义 |
|------|------|
| 执行轨迹（Trace） | 一个 Change 从开始到归档的完整过程记录 |
| 数据飞轮（Flywheel） | 持续采集→分析→改进→再采集的自动化闭环 |
| 轨迹标签（Tag） | 对轨迹按多维度分类的元数据（变更类型/复杂度等） |
| 上下文需求清单 | 每个阶段明确列出需要从上游工件加载的字段 |
| 轻量摘要 | 仅保留当前阶段必选字段的工件精简版 |
| 闭环校准 | 将评分与实际结果建立统计关联并调整权重 |
| Gap 分析 | 按标签分片对比各维度表现，定位薄弱环节 |
| 顿悟信号 | 同一根因多次出现后自动触发的进化建议 |
