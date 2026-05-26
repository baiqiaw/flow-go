# Scars — 疤痕协议

> 借鉴 Meta_Kim 的疤痕协议。记录系统性治理失败的预防性知识。
> 与 LESSONS 互补：LESSONS = 正向知识（学到了什么），Scars = 反向知识（在哪栽过跟头）。

---

## 目录结构

```
.specs/
├── <change-id>/          ← 归档时移动到 archive/
├── scars/                ← 全局目录，与 <change-id>/ 同级
│   └── YYYY-MM-type-short-desc.md
├── adr/                  ← 全局目录（已有）
├── CONTEXT.md            ← 全局文件（已有）
└── evolution/            ← 全局目录（已有）
```

疤痕文件放在 `.specs/scars/` 下（全局），归档流程只移动 `.specs/<change-id>/` 子目录，疤痕不会被清理。

---

## 疤痕格式

```markdown
---
id: YYYY-MM-type-short-desc
type: overstep | gate-bypass | process-gap | false-positive
trigger: 热修 | 闸门绕过 | 需求返工 | 审查 > 2 轮 | 活体验证 bug > 3
impact: none | degraded | recovered | critical
created: YYYY-MM-DD
---

## 根因
<一句话描述系统性原因，不是任务级错误>

## 预防规则
<一条具体可执行的预防规则，下次遇到类似场景时直接引用>
```

### type 判定标准

| type | 含义 | 典型场景 |
|------|------|---------|
| overstep | 角色越权，跨阶段做了不该做的事 | 需求阶段写了实现方案、开发阶段改了需求 |
| gate-bypass | 闸门被绕过或跳过 | 热修绕过审查、以"太简单"跳闸门 |
| process-gap | 流程有系统性漏洞 | 审查 3+ 轮才通过、测试漏了边界用例 |
| false-positive | 误报，事后看不是真正的问题 | 闸门误判、风险未实际发生 |

### impact 判定标准

| impact | 含义 |
|--------|------|
| none | 未产生实际影响（及时发现） |
| degraded | 产生部分影响但可恢复 |
| recovered | 产生严重影响但已完全恢复 |
| critical | 产生严重影响且留有后遗症 |

---

## 写入时机

在 7-验收阶段步骤 6（LESSONS 提名）后、步骤 7（进化反思）前，新增步骤 6A 疤痕评估。

### 触发条件

以下事件发生时**必须评估**是否写入疤痕（STANDARD/HEAVY 复杂度写入，LITE 仅评估不写入）：

| 事件 | 默认 type | 评估问题 |
|------|----------|---------|
| 热修发生 | gate-bypass | "这次热修是否暴露了流程漏洞？" |
| 审查 > 2 轮才通过 | process-gap | "多轮审查是因为需求/设计有系统性遗漏吗？" |
| 活体验证 bug > 3 | process-gap | "bug 集中出现是否因为某个阶段质量检查不足？" |
| 需求返工（设计阶段推翻需求） | overstep | "需求阶段的澄清或意图验证是否不足？" |

评估结果：
- 是系统性问题 → 写入疤痕
- 是偶发问题 → 不写入，但可在 LESSONS 中记录
- 不确定 → 写入（type: false-positive），后续可清理

### 疤痕清理

7-验收步骤 6A 中可选择性清理：
- impact = none 且创建时间 > 90 天 → 可删除（预防规则已融入流程）
- type = false-positive 且创建时间 > 30 天 → 可删除

---

## 扫描时机

在 0-需求阶段步骤 0（问题空间回退检查）后，新增步骤 0A 疤痕扫描。

### 扫描流程

1. 检查 `.specs/scars/` 目录是否存在且非空
2. 不存在或为空 → 静默跳过
3. 存在且有文件 → 读取所有疤痕文件
4. 按 trigger 类型与当前变更特征匹配：
   - 当前是热修 → 匹配 gate-bypass 类疤痕
   - 当前涉及 ≥3 模块 → 匹配 process-gap 类疤痕
   - 当前是 bugfix → 匹配 process-gap 和 overstep 类疤痕
   - 其他 → 匹配所有疤痕（但只展示 impact ≥ degraded 的）
5. 匹配到 → 输出警告：「⚠️ 历史疤痕：{预防规则}（来源：{id}）」

所有复杂度都执行疤痕扫描（LITE 也扫描，只是 LITE 不写入新疤痕）。
