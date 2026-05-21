# 核心脚本示例数据

用于开发调试和回归测试。每个脚本提供 `sample_input.json` + `expected_output.json` 对。

## 用法

```bash
# health_scorer — 输入输出测试
python3 health_scorer.py assets/health_scorer_sample_input.json --format json
# 对比输出与 assets/health_scorer_expected_output.json

# risk_analyzer — 输入输出测试
python3 risk_analyzer.py assets/risk_analyzer_sample_input.json --format json
# 对比输出与 assets/risk_analyzer_expected_output.json

# gap_analyzer — 需要 .specs 目录结构
# 示例 traces 数据在 evolution_signal_sample_traces.jsonl
# 需拷贝到 .specs/traces.jsonl 后运行

# evolution_signal — 需要 .specs/<change-id>/ 目录结构
# 需创建包含工件文件的 .specs 目录后运行
```

## 文件清单

| 文件 | 说明 |
|------|------|
| `health_scorer_sample_input.json` | 健康评分器输入（AC/测试/评审/代码/工件数据） |
| `health_scorer_expected_output.json` | 预期输出（7 维评分 + RAG + 干预优先级） |
| `risk_analyzer_sample_input.json` | 风险分析器输入（3 项风险） |
| `risk_analyzer_expected_output.json` | 预期输出（评分 + EMV + 应对策略） |
| `evolution_signal_sample_traces.jsonl` | 轨迹样本数据（3 条 Change 轨迹） |
