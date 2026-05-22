# SUMMARY — CH-20260522-001

## 改动概览
借鉴 Karpathy Skills 的 4 条行为准则，对 flow-go 的 references/ 体系进行 5 项优化。

## 任务完成情况

### T01 — SKILL.md 权衡声明 + 锚点口诀 + 直觉检验 ✅
- 在流程全景后插入权衡声明（2 行）
- 角色声明模板增加 `✅ 阶段锚点` 行 + 8 阶段口诀表
- 精炼环在反模式清零后增加直觉检验步骤（步骤 3）

### T02 — gate-rules.md 锚点引用 ✅
- §4 的 3-开发、4-测试、5-审查 反模式子节各增加 `> 锚点：...` 引用

### T03 — 反模式实例对照 ✅
- 新增 `references/anti-pattern-examples.md`
- 包含 6 组 ❌/✅ 对照：scope-creep、over-engineering、drive-by-refactor、skip-clarification、fake-verify、weaken-failing
- 每组有伪代码 + 关键差异总结

### T04 — 归档成功指标 ✅
- special-flows.md 归档流程步骤 9 和 10 之间插入步骤 9.5
- 3 条成功指标：Diff 无关改动、假设返工、澄清时机

## 验证闭环
- 功能不变 ✅：仅增加文档内容，未改变流程行为
- verify 全通过 ✅：4 个任务的 grep 验证均通过
- 精炼环 ✅：无越界改动、无新增依赖、改动可追溯到 AC

## 文件改动清单
| 文件 | 操作 | 改动量 |
|------|------|--------|
| SKILL.md | 修改 | +20 行（权衡声明 + 口诀表 + 直觉检验） |
| references/gate-rules.md | 修改 | +3 行（锚点引用） |
| references/anti-pattern-examples.md | 新增 | ~150 行（6 组对照） |
| references/stages/special-flows.md | 修改 | +5 行（成功指标） |
