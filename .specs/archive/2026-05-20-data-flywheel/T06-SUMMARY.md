# SUMMARY — T06

## 做了什么
在 8 个阶段指南文件末尾追加「上下文需求清单」章节。0-需求阶段注明"首个阶段，无上游依赖"，其余 7 个阶段按 DESIGN.md 第 7 节定义的表格内容追加（来源工件/字段/必选或可选/保留方式）。

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|
| references/stages/0-requirement.md | 修改 | 追加"首个阶段，无上游依赖" |
| references/stages/1-design.md | 修改 | 8 条需求（REQUIREMENT+CONTEXT） |
| references/stages/2-task.md | 修改 | 6 条需求（REQUIREMENT+DESIGN） |
| references/stages/3-develop.md | 修改 | 8 条需求（REQUIREMENT+DESIGN+TASK+CONTEXT） |
| references/stages/4-test.md | 修改 | 3 条需求（REQUIREMENT+TASK+SUMMARY） |
| references/stages/5-review.md | 修改 | 6 条需求（REQUIREMENT+DESIGN+SUMMARY+TEST） |
| references/stages/6-deploy.md | 修改 | 3 条需求（REVIEW+CHANGE+DESIGN） |
| references/stages/7-acceptance.md | 修改 | 3 条需求（REQUIREMENT+CHANGE+DEPLOY） |

## Verify 输出
```
$ grep -l "上下文需求清单" references/stages/*.md | wc -l
8
```

## 沿用既有抽象
- DESIGN.md 第 7 节表格格式 → 沿用

## 越界检查
- TASK write_files：8 项（references/stages/*.md）
- 实际 diff 涉及：8 项
- 越界：0

## 已知问题
- 无

## 交叉评审
doc 类型任务，跳过交叉评审。

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 1/1（首次） |
| 交叉评审轮次 | N/A（doc 类型） |
| 代码行数变化 | +86 |
| 改动文件数 | 8 个 |
| 沿用既有抽象 | 1 个沿用 / 0 个新建 |
