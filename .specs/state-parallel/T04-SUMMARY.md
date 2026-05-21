# SUMMARY — T04

## 做了什么
更新 special-flows.md 中 7 个流程的 STATE.md 读写路径：归档（含 Pipeline 衔接）、中断、并行启动、废弃、回溯、热修、归档维护。所有涉及 `活跃 Change`/`当前阶段`/`当前任务`/`中断任务`/`阶段进度` 的读写改为 per-change STATE.md；`活跃 Change` 的增删操作同时更新索引表。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/stages/special-flows.md | 修改 | 6 个流程适配双文件结构，归档维护确认无需修改 |

## Verify 输出
```
索引表引用: 25
per-change STATE引用: 21
归档清理操作: 6
```

## 越界检查
- TASK write_files：1 项
- 实际 diff 涉及：1 项
- 越界：0

## 已知问题
- 无
