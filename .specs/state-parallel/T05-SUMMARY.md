# SUMMARY — T05

## 做了什么
更新 validate_state.py 和 gate_check.py 以支持新的两层 STATE.md 结构。validate_state.py 新增项目级/per-change/一致性三层校验、旧格式检测、--change-id 参数。gate_check.py 新增 --change-id 必需参数，从 per-change STATE.md 读取当前阶段。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/scripts/validate_state.py | 修改 | 三层校验（项目级+per-change+一致性）+ 旧格式检测 + --change-id |
| references/scripts/gate_check.py | 修改 | --change-id 必需 + 从 per-change STATE 读阶段 |

## Verify 输出
```
validate_state.py: 24 处新格式引用
gate_check.py: 17 处 change-id 引用
语法检查: 两个文件均通过
```

## 越界检查
- TASK write_files：2 项
- 实际 diff 涉及：2 项
- 越界：0

## 已知问题
- 无
