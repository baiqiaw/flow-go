# SUMMARY — T10

## 做了什么
在 trace_collector.py 中新增 --check-outcome 模式（与 --change-id 互斥）。执行时读取 traces.jsonl 中 outcome==null 的记录，扫描 .specs/archive/ 下 ABANDONED.md（→ abandoned）或含热修标记的 CHANGE.md（→ hotfixed）。无引用且超过 outcome_days 天 → 更新为 success。原地替换 traces.jsonl 对应行。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/scripts/trace_collector.py | 修改 | 新增 --check-outcome 模式 + check_outcome 函数 |

## Verify 输出
```
$ python3 trace_collector.py --help 2>&1 | grep -q "check-outcome"
$ echo $?
0
```

功能测试：创建含 ABANDONED.md 的归档目录，traces.jsonl 中 outcome=null 的记录被正确更新为 abandoned。

## 沿用既有抽象
- trace_collector.py 现有 CLI → 沿用（argparse 互斥组）
- read_file 工具函数 → 沿用

## 越界检查
- TASK write_files：1 项（references/scripts/trace_collector.py）
- 实际 diff 涉及：1 项
- 越界：0

## 已知问题
- 无

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 1/1（首次） |
| 代码行数变化 | +65 |
| 改动文件数 | 1 个 |
| 沿用既有抽象 | 2 个沿用 / 0 个新建 |
