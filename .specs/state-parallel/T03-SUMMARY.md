# SUMMARY — T03

## 做了什么
将 8 个 stage 文件中的「更新 STATE.md 的 `阶段进度` 字段」改为「更新 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段」，「会话恢复时读 `阶段进度`」改为读 per-change STATE。3-develop.md 的中断任务写入目标也同步更新。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/stages/0-requirement.md | 修改 | 阶段进度写入目标 |
| references/stages/1-design.md | 修改 | 同上 |
| references/stages/2-task.md | 修改 | 同上 |
| references/stages/3-develop.md | 修改 | 中断任务+阶段进度写入目标 |
| references/stages/4-test.md | 修改 | 阶段进度写入目标 |
| references/stages/5-review.md | 修改 | 同上 |
| references/stages/6-deploy.md | 修改 | 同上 |
| references/stages/7-acceptance.md | 修改 | 同上 |

## Verify 输出
```
旧引用: (无)
新引用数: 8
阶段进度字段仍在: 3
```

## 越界检查
- TASK write_files：8 项
- 实际 diff 涉及：8 项
- 越界：0

## 已知问题
- 无
