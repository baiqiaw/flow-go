# SUMMARY — T03

## 做了什么
在归档流程步骤 4 和 5 之间插入步骤 4.5（轨迹采集）：执行 trace_collector.py 生成 TRACE.md 和追加 traces.jsonl，采集失败不阻塞归档。在归档自检清单新增一项。在废弃流程末尾新增步骤 9（outcome 标记）：更新 traces.jsonl 中该 change-id 的 outcome 为 abandoned。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/stages/special-flows.md | 修改 | 归档+废弃流程新增轨迹相关步骤 |

## Verify 输出
```
$ grep -c "trace_collector" references/stages/special-flows.md
2
```

## 沿用既有抽象（grep 结果）
- special-flows.md 现有步骤格式 → 沿用（编号 + 动作描述）

## 越界检查
- TASK write_files：1 项（references/stages/special-flows.md）
- 实际 diff 涉及：1 项
- 越界：0

## 已知问题
- 无

## 交叉评审
doc 类型任务，跳过交叉评审。可读性自检：步骤编号连贯（4→4.5→5），自检清单完整。

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 1/1（首次） |
| 交叉评审轮次 | N/A（doc 类型） |
| 代码行数变化 | +4 |
| 改动文件数 | 1 个 |
| 沿用既有抽象 | 1 个沿用 / 0 个新建 |
