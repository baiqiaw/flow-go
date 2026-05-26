# CHANGE — feat-dev-optimize

## Why（为什么做）
- **痛点场景**：flow-go 在设计阶段依赖主代理单线程探索代码库，交叉评审缺少置信度过滤导致噪音多，设计产出缺少多方案对比
- **当前障碍**：主代理在广度探索中消耗大量 token；评审子代理报告所有问题无优先级区分；DESIGN.md 模板没有备选方案章节
- **不做后果**：token 成本居高不下；评审效率低，真正重要的问题被噪音淹没；设计方案缺乏权衡分析导致后续返工

## What（做什么）
借鉴 Anthropic 官方 feature-dev skill 的并行子代理模式，对 flow-go 进行 5 项优化：
1. 在 1-设计阶段引入并行子代理探索（2-3 个 explorer 并行，返回关键文件列表）
2. 在交叉评审子代理中引入置信度过滤（≥80 才报告）
3. 在 DESIGN.md 模板增加「备选方案」章节（STANDARD/HEAVY 强制）
4. 子代理指定 model: sonnet 降低 token 成本
5. 在 5-审查阶段引入并行 reviewer（3 个 reviewer 并行聚焦不同维度）

## 影响面
- 涉及模块：references/stages/1-design.md、references/stages/5-review.md、references/artifacts/spec-artifacts.md、references/cross-review-matrix.md
- 数据库变更：否
- API 变更：否
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- 不修改 flow-go 主流程编排（references/stages/special-flows.md 等）
- 不修改状态管理机制（STATE.md 相关逻辑）
- 不修改 0-需求、2-任务、3-开发、4-测试、6-部署、7-验收阶段文件
- 不引入新的外部依赖或 MCP Server

## 验收线
5 项改进全部落实到对应的 reference 文件中，交叉评审 6 维全 PASS。

## 路径建议
增量，理由：改动集中在 references/ 目录下的 4-5 个文件，不涉及主流程编排或状态管理；项目已有 CI/CD 管线但属于内部工具。

## 验证假设

| # | 假设 | 证据级别 | 验证方式 | 验证阶段 | 推翻信号 |
|---|------|---------|---------|---------|---------|
| 1 | 并行子代理探索在设计阶段能减少主代理 token 消耗 | C | 设计阶段实际 token 消耗对比 | 1-设计 | 并行启动开销 > 节省的 token |
| 2 | 置信度过滤 ≥80 阈值能过滤掉大部分误报 | C | 交叉评审输出质量对比 | 5-审查 | 高价值问题被过滤 |
| 3 | 子代理使用 sonnet 模型不会显著降低探索质量 | B | sonnet/opus 探索结果对比 | 1-设计 | sonnet 遗漏关键文件 |

## 终止条件

| # | 条件 | 触发阶段 | 触发后动作 |
|---|------|---------|----------|
| 1 | 并行子代理在 bash/skill 层面无法可靠启动 | 1-设计 | 回退到 1-设计，降级为单线程探索 |
