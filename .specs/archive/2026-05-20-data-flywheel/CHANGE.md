# CHANGE — data-flywheel

## Why（为什么做）
flow-go 已有进化分析（evolution_signal/reflect）和健康评分（health_scorer），但缺乏系统化的执行数据采集和评分闭环。借鉴 Shopify 工程团队的数据飞轮方法论，将 flow-go 从"偶尔反思"升级为"持续积累、自动改进"的数据驱动体系。

## What（做什么）
为 flow-go 增加 6 项数据驱动优化能力，形成完整的数据飞轮：
1. **执行轨迹自动采集** — 每个 Change 归档时自动记录完整的阶段流转路径、关键决策和健康评分
2. **工件格式有效性验证** — 分析 Markdown 工件模板的 token 效率，识别冗余格式和未使用字段
3. **健康评分闭环校准** — 将健康评分与变更实际结果（回滚/热修/投诉）建立统计关联，校准权重
4. **多维标签 Gap 分析** — 对执行轨迹按多维度打标，分片定位薄弱环节
5. **飞轮自动化** — 周期性自动巡检轨迹数据，运行分析并生成周报
6. **上下文轻量摘要** — 各阶段仅加载所需上下文摘要，减少无效 token 消耗

## 影响面
- 涉及模块：references/scripts/（5 个新脚本：trace_collector.py、artifact_format_analyzer.py、health_calibration.py、gap_analyzer.py、context_summarizer.py）、references/stages/（8 个阶段指南修改）、references/artifacts/（meta-artifacts.md 修改）、SKILL.md（状态更新逻辑修改）、special-flows.md（归档流程修改）
- 数据库变更：否
- API 变更：否
- 依赖变更：否（继续使用 Python 标准库）
- CONTEXT 需更新：是（新增数据飞轮相关配置项和路径）

## 范围排除（这次不做）
- 不涉及 LLM fine-tuning（flow-go 是 prompt 驱动的，不是模型训练）
- 不引入第三方 Python 依赖
- 不改变 flow-go 的核心状态机架构（STATE.md 仍为唯一状态源）
- 不修改现有脚本的接口签名（只新增，不破坏）
- 不做跨项目数据共享（traces.jsonl 仅限当前项目）

## 验收线
6 项优化全部完成设计文档，包括：新增脚本接口定义、工件格式定义、阶段指南修改清单、配置项定义。设计需通过交叉评审 6 维全 PASS。

## 路径建议
完整路径（0→1→2→3→4→5→6→7），理由：涉及 6 个独立模块，影响面广，需完整的闸门检查。分 3 批实施：P0（轨迹采集+上下文优化）→ P1（标签分析+评分闭环）→ P2（格式验证+飞轮自动化）。
