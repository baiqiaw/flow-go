# 优先级框架快速参考

> flow-go 2-任务阶段的任务排序辅助。按需 grep 加载，禁止整读。

---

## 框架选择

```
任务 ≤ 3？→ 不需要框架，按依赖顺序执行
任务 > 3 且有量化数据？→ RICE
任务 > 3 且时间紧迫？→ ICE
其他 → MoSCoW（默认）
```

---

## MoSCoW（默认）

- **Must**：不完成则整个 change 无意义（AC 硬性要求）
- **Should**：重要但可延迟（核心体验优化）
- **Could**：锦上添花（边界情况、体验细节）
- **Won't**：这次明确不做（已在 REQUIREMENT 范围排除中）

操作：给 task 标注级别，Must 先做，Could 最后。

---

## ICE（快速评分）

适用：任务 > 5 个，需量化排序但无精确数据。

`ICE = (Impact + Confidence + Ease) ÷ 3`，每项 1-10 分。

| 维度 | 1-3 | 4-6 | 7-10 |
|------|-----|-----|------|
| Impact | 仅影响边缘功能 | 影响核心功能之一 | 影响 AC 关键路径 |
| Confidence | 实现方案不确定 | 有参考但需调整 | 有成熟方案/复用 |
| Ease | 需新增依赖/大重构 | 局部改动 | 纯增量/复用既有 |

---

## RICE（精确评分）

适用：有用户数据或收益预估。

`RICE = (Reach × Impact × Confidence) ÷ Effort`

| 维度 | 说明 | 值域 |
|------|------|------|
| Reach | 影响的用户/场景数 | 实际数字 |
| Impact | 单用户影响度 | 0.25/0.5/1/2/3 |
| Confidence | 把握程度 | 0.5/0.8/1.0 |
| Effort | 预估工时 | 小时数 |

---

## TASK.xml 用法

```xml
<task id="T01" parallel="true" priority="must">
<task id="T02" parallel="false" priority="should" ice="7.3">
<task id="T03" parallel="false" priority="could" rice="245">
```

**规则**：
- 排序后 `priority` 必须填（must/should/could），未排序的 task 无此属性
- `ice` / `rice` 可选数值，任务 > 5 个时建议填写
- 执行顺序：优先级 > 评分 > 依赖拓扑
