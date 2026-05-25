# CHANGE — autoresearch-borrow

## Why（为什么做）
分析 autoresearch（GitHub 2.1k star Claude Code 插件）后，发现 flow-go 缺少 4 个关键机制：开发中实时回归防护（Guard）、基于 Git 历史的记忆增强、开发/测试停滞自动检测（Plateau）、以及结构化可机读的迭代日志。这些缺失会导致「改一处坏十处」的返工、跨会话恢复不精准、在死胡同浪费 token。

## What（做什么）
从 autoresearch 借鉴 4 个经过验证的机制，融入 flow-go 的 3-开发和 4-测试阶段：
1. **Guard 机制**：TASK.md 增加 guard 字段，3-开发阶段每个 task 完成后自动运行 guard 命令验证无回归
2. **Git as Memory**：回溯流程和精炼环增加 git log/diff 读取，利用历史记录避免重复失败方案
3. **Plateau 检测**：3-开发和 4-测试阶段增加停滞检测，连续 N 轮无进展自动升级策略
4. **结构化迭代日志**：在 .specs/<id>/ 增加 iterations.tsv，记录每个 task/测试的原子结果

## 影响面
- 涉及模块：SKILL.md、references/stages/3-develop.md、references/stages/4-test.md、references/stages/special-flows.md、references/artifacts/task-artifacts.md
- 数据库变更：否
- API 变更：否
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- P2 多维度测试矩阵（12 维度测试覆盖）
- P2 交互式批量问答优化
- P3 Chain 机制（灵活子流程组合）
- P3 噪声处理（不稳定指标验证）
- 不修改 flow-go 的路由逻辑或状态管理核心

## 验收线
4 个机制全部实现，用一个示例 change 实际走一遍流程验证 Guard/Git/Plateau/TSV 机制生效。

## 路径建议
增量，理由：改动涉及多文件但无需部署阶段，验收需实际流程测试。
