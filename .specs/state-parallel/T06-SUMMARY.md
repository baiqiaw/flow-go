# SUMMARY — T06

## 做了什么
更新 2 个 Python 脚本的 STATE.md 读取路径（trace_collector.py 改为读 per-change STATE；evolution_signal.py 改为从 specs_dir 直接读 STATE.md）。更新 3 个文档文件（.codex/instructions.md 和 README.md 的状态架构描述改为两层结构）。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/scripts/trace_collector.py | 修改 | read_state 改为读 .specs/<id>/STATE.md |
| references/scripts/evolution_signal.py | 修改 | _extract_hotfix 改为从 specs_dir 读 STATE.md |
| .codex/instructions.md | 修改 | 状态管理描述改为两层结构 |
| README.md | 修改 | 状态驱动描述改为两层结构 |

注：sync-workflow.md 经检查无 STATE.md 字段级引用，无需修改。

## Verify 输出
```
trace_collector: 2 处 per-change 引用
evolution_signal: 12 处相关引用
instructions.md: 3 处新引用
README.md: 4 处新引用
```

## 越界检查
- TASK write_files：5 项（实际改 4 项，sync-workflow.md 无需改动）
- 实际 diff 涉及：4 项
- 越界：0

## 已知问题
- 无
