# SUMMARY — T09

## 做了什么
创建 health_calibration.py 健康评分校准脚本。读取 traces.jsonl 中 outcome != null 的记录，用 Spearman 排名相关系数计算各维度与 outcome 的相关性，对比 health_scorer.py 的当前权重输出校准建议（suggested_weight）。样本不足输出警告退出码 2。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/scripts/health_calibration.py | 新增 | 健康评分校准脚本，166 行 |

## Verify 输出
```
$ python3 references/scripts/health_calibration.py --help 2>&1 | grep -q "health_calibration"
$ echo $?
0
```

## 沿用既有抽象
- health_scorer.py DIMENSIONS 权重常量 → 沿用（CURRENT_WEIGHTS）
- Spearman 排名相关：statistics 模块手动实现（无需 numpy）

## 越界检查
- TASK write_files：1 项
- 实际 diff 涉及：1 项
- 越界：0

## 已知问题
- 无

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 1/1（首次） |
| 代码行数变化 | +166 |
| 改动文件数 | 1 个 |
| 沿用既有抽象 | 2 个沿用 / 0 个新建 |
