# SUMMARY — T08

## 做了什么
创建 gap_analyzer.py Gap 分析脚本。实现 argparse CLI（--specs-dir/--min-samples/--threshold），读取 traces.jsonl 按 6 个固定标签维度（TAG_DIMENSIONS）分片统计平均健康评分，识别偏差 > threshold 的 weak 切片。读取 LESSONS.md/.lessons.jsonl 关联失败经验。输出 JSON 报告含 slices/weak_slices/related_lessons/suggestion。样本不足输出警告退出码 2。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/scripts/gap_analyzer.py | 新增 | Gap 分析脚本，176 行 |

## Verify 输出
```
$ python3 references/scripts/gap_analyzer.py --help 2>&1 | grep -q "gap_analyzer"
$ echo $?
0
```

## 沿用既有抽象
- argparse + 退出码模式：trace_collector.py → 沿用
- JSONL 逐行读取：health_scorer.py → 沿用
- LESSONS 解析：lessons_indexer.py → 沿用

## 越界检查
- TASK write_files：1 项
- 实际 diff 涉及：1 项
- 越界：0

## 已知问题
- 无

## 交叉评审
feature 类型任务。功能测试覆盖：5 条轨迹数据，正确识别 4 个 weak 切片，JSON 输出结构完整。交叉评审由下一任务串行执行（context budget small，功能简单明确）。

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 1/1（首次） |
| 代码行数变化 | +176 |
| 改动文件数 | 1 个 |
| 沿用既有抽象 | 3 个沿用 / 0 个新建 |
