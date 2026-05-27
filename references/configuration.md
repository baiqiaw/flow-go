# flow-go 配置参考

读取顺序：项目级 `.flowgo-config` → 用户级 `~/.flowgo-config` → 内置默认值。

格式：YAML，每行一个键值对。

## 配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `test_rounds` | 3 | 4-测试阶段单轮修复上限 |
| `test_depth` | standard | 4-测试阶段默认深度（smoke / standard / deep） |
| `max_files_per_task` | 10 | 3-开发阶段单任务改动文件上限 |
| `auto_sync` | true | 决策信号自动触发知识库受作用域同步 |
| `priority_framework` | MoSCoW | 2-任务阶段默认优先级框架（auto=按决策树自动选择，MoSCoW/WSJF/RICE/ICE/MCDA=强制指定） |
| `explain_level` | default | 解释详细度（default / terse） |
| `output_mode` | normal | normal / tight / caveman / ultra | 输出压缩级别，按阶段自动切换 |
| `evolution_mode` | auto | 进化分析模式（auto=自动触发 / off=关闭） |
| `complexity_threshold` | 5 | blast-radius 文件数阈值 |
| `bitter_pill_auto` | true | 归档后自动触发苦丸审计 |
| `preflight_check` | true | 2-任务阶段启用预检环（反幻觉+粒度+上下文预算） |
| `context_budget_mode` | auto | 上下文预算模式（auto=自动估算 / manual=手动填写 / off=关闭） |
| `flywheel_min_samples` | 3 | 飞轮分析最小轨迹样本数 |
| `flywheel_gap_threshold` | 1.5 | Gap 分析偏差阈值（分） |
| `flywheel_outcome_check` | true | 是否自动检测归档后 outcome |
| `flywheel_outcome_days` | 7 | outcome 自动检测窗口（天） |
| `context_summarize` | false | 是否默认启用上下文摘要（false=全文加载，true=摘要加载） |
| `trace_auto_collect` | true | 归档时是否自动采集轨迹 |
| `user_input_capture` | true | 是否记录用户输入到 user-inputs.jsonl |
| `guard_enabled` | true | 3-开发阶段启用 Guard 回归防护 |
| `guard_timeout` | 30 | Guard 命令超时秒数，超时视为通过并告警 |
| `git_memory_depth` | 20 | 回溯/精炼环读取 git 历史的 commit 数量 |
| `stagnation_patience` | 3 | 3-开发/4-测试阶段连续失败多少轮触发 Plateau 告警 |
| `iteration_log` | true | 是否在 .specs/<id>/iterations.tsv 记录结构化迭代日志 |

## 示例

```yaml
test_rounds: 3
test_depth: standard
priority_framework: MoSCoW
explain_level: default
preflight_check: true
guard_enabled: true
iteration_log: true
```
