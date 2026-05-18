# 任务工件模板

> TASK.md / SUMMARY.md / PROGRESS.md — 2~3 阶段产出。

---

## 交叉评审前自检清单

> 在 dispatch 交叉评审子代理之前，逐项检查。全部通过后才调用子代理。

### TASK.md 自检
- [ ] 依赖图无循环引用
- [ ] 每个任务有 verify 命令（可执行）
- [ ] 每个任务有 type 属性（feature/bugfix/refactor/doc）
- [ ] depends_on 引用的任务 ID 均存在
- [ ] 并行标记合理（无依赖的任务标为 parallel）

### SUMMARY.md 自检
- [ ] 改动文件表已填写（非空）
- [ ] verify 输出是真实命令输出（非"通过"二字）
- [ ] 越界检查：diff 文件数 ≤ TASK write_files 数
- [ ] 沿用既有抽象有 grep 结果（非猜测）

---

## TASK.md（.specs/<id>/TASK.md）

```markdown
# TASK — <change-id>

## 依赖图
<用文字描述任务依赖关系和并行标记>

## 任务列表

<task id="T01" parallel="true" priority="must" type="feature">
  <name>任务名称</name>
  <read_files>src/module/*</read_files>
  <write_files>src/module/NewFeature.ts</write_files>
  <action>实现描述</action>
  <verify>npm test -- module/NewFeature.test.ts</verify>
  <done>测试通过，功能符合 AC-1</done>
  <depends_on></depends_on>
</task>

<task id="T02" parallel="false" priority="should" type="bugfix">
  <name>依赖 T01 的任务</name>
  <read_files>src/module/NewFeature.py</read_files>
  <write_files>src/module/integration.py</write_files>
  <action>集成实现</action>
  <verify>pytest tests/test_integration.py -v</verify>
  <done>集成测试通过</done>
  <depends_on>T01</depends_on>
</task>

<!--
type 取值（必填）：
  feature  — 新功能开发（默认）
  bugfix   — 缺陷修复
  refactor — 重构/优化
  doc      — 文档/注释
  config   — 配置变更
  chore    — 杂项维护（依赖更新/清理/工具升级等）
从 REQUIREMENT.md 描述推断：含"修复/fix/bug"→bugfix，"重构/refactor"→refactor，"文档/doc"→doc，"配置/config/环境"→config，"升级/清理/依赖"→chore，其余→feature
-->
```

---

## SUMMARY.md（.specs/<id>/<task-id>-SUMMARY.md）

```markdown
# SUMMARY — <task-id>

## 做了什么
<简述>

## 改动文件
| 文件 | 变更类型 | 说明 |
|------|---------|------|

## Verify 输出
<贴出真实命令输出>

## 沿用既有抽象（grep 结果）
- HTTP 请求：找到 src/lib/api-client.ts → 沿用
- 日期格式化：未找到 → 新建

## 越界检查
- TASK write_files：N 项
- 实际 diff 涉及：N 项
- 越界：0

## 已知问题
- <无 / 列出>

## 交叉评审（独立子代理）
> 维度定义以 `references/cross-review-matrix.md`（矩阵 B）为准，下表展示格式示例。
### 评审轮次: N/3
### 评审矩阵
| 维度 | 结果 | 说明 |
|------|------|------|
| 规格合规 | PASS/FAIL | 实现 vs task action/done + DESIGN |
| 设计对齐 | PASS/FAIL | 实现路径遵循 DESIGN 方案 |
| 测试证据 | PASS/FAIL | verify 输出真实 + 文件齐全 |
| 边界卫生 | PASS/FAIL | diff 无越界 + 无无关改动 |
| 反幻觉 | PASS/FAIL | 无虚构 import/API/配置 |
| 质量底线 | PASS/FAIL | 无 bug/无密钥/无空 catch |

### 发现问题
- <无 / 逐条列出>

### 修复记录
| 轮次 | 问题 | 修复 | re-verify |
|------|------|------|----------|

## 量化指标
| 指标 | 值 |
|------|-----|
| verify 通过率 | 1/1（首次） / N/M（总） |
| 交叉评审轮次 | N/3 |
| 代码行数变化 | +N / -M |
| 改动文件数 | N 个 |
| 沿用既有抽象 | N 个沿用 / M 个新建 |
```

---

## PROGRESS.md（.specs/<id>/<task-id>-PROGRESS.md，临时）

<!-- 生命周期：创建于 3-开发中断 → 删除于任务完成 / spec归档 / spec废弃 -->

```markdown
# PROGRESS — <task-id>（临时文件）

## 已完成子步骤
- [x] 步骤 A
- [ ] 步骤 B

## 当前正在做
<一段话，恢复后能直接续上>

## 已排除方案
| 方案 | 理由 | 失败次数 |
|------|------|---------|

## 待确认假设
- <假设 1>

## 元信息
- 创建时间：<YYYY-MM-DD>
- 关联任务：<task-id>
```
