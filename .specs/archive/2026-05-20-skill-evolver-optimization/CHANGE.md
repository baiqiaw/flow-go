# CHANGE — skill-evolver-optimization

## Why（为什么做）
借鉴 Skill Evolver（Karpathy autoresearch + Stanford Meta-Harness + Anthropic skill-creator）的自进化思想，flow-go 已有门控、轨迹采集、进化信号等基础设施，但缺少**闭环**——从 trace 提取信号后不驱动改进、门控维度不完整、评测无分层。本次优化补齐这些缺口。

## What（做什么）
1. gate_check.py 补第 5 维"效率"门控（AC 通过数 vs 代码行数比值）
2. 进化分析闭环：归档时自动运行 evolution_signal.py，信号写入 LESSONS.md"待改进"章节，开发阶段自动加载相关信号
3. gate_check.py 增加 L1/L2/L3 分层评测模式（秒级→分钟级→条件触发）
4. 3-开发阶段增加可选 auto-verify：每完成子任务自动跑 L1 门卫 + git stash 回滚建议（L1 门卫为 auto-verify 提供低成本检查基础，auto-verify 产出的检查结果成为效率维度的数据源，形成闭环）
5. evolution_reflect.py 增加 6 级优先级路由输出

## 影响面
- 涉及模块：references/scripts/gate_check.py, references/scripts/evolution_signal.py, references/scripts/evolution_reflect.py, references/stages/3-develop.md, references/stages/special-flows.md
- 配置文件变更：是（.flowgo-config 新增 auto_verify 配置项）
- 数据库变更：否
- API 变更：否
- 依赖变更：否
- CONTEXT 需更新：否

## 范围排除（这次不做）
- 不做 holdout/训练集分离（需要 evals.json 改造，范围过大）
- 不做 SKILL.md 主文件改动（优化效果验证后再改路由）
- 不做自动 git revert（仅建议 git stash）

## 验收线
gate_check.py 支持 5 维门控 + 分层评测模式；进化分析形成 trace→signal→LESSONS 闭环；开发阶段可 auto-verify；evolution_reflect 输出优先级建议

## 路径建议
增量，理由：在现有脚本基础上扩展，不改动整体架构
