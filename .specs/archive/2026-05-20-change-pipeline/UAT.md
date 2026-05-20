# UAT — change-pipeline

## 验收准则逐项验证

| AC | 标题 | 验证方式 | 结果 |
|----|------|---------|------|
| AC-1 | 拆分时自动创建 PIPELINE.md | 0-requirement.md 步骤2含 PIPELINE.md 创建 | PASS |
| AC-2 | PIPELINE.md 格式（7列表格） | meta-artifacts.md 含完整模板+约束 | PASS |
| AC-3 | 归档后自动衔接 | special-flows.md 步骤8.5 + SKILL.md 步骤7 | PASS |
| AC-4 | 用户确认后自动启动 | SKILL.md 步骤1第6点含完整启动流程 | PASS |
| AC-5 | 排队管理命令 | SKILL.md 路由表 + frontmatter 含触发词 | PASS |
| AC-6 | 依赖检查 | 0-requirement.md 含依赖声明 | PASS |
| AC-7 | 归档时状态更新 | special-flows.md 步骤8.1 active→completed | PASS |
| AC-8 | 无 PIPELINE 时不影响 | 所有新增逻辑有"如存在"条件 | PASS |
| AC-8.1 | 跨会话 Pipeline 待续恢复 | SKILL.md 步骤1 + 回溯步骤2 | PASS |
| AC-8.2 | 暂不执行保留提示 | special-flows.md 步骤8.5 含"用户拒绝→保留" | PASS |
| AC-9 | 中断而非归档 | special-flows.md 含独立中断流程 | PASS |
| AC-10 | 中断恢复 STATE.md 扫描 | 回溯步骤11 含未归档扫描 | PASS |
| AC-11 | 多 change 并行状态 | meta-artifacts.md 并行 Change 字段 + 并行启动流程 | PASS |
| AC-12 | 并行冲突检测文件范围 | 并行启动流程含 glob 重叠检测 | PASS |
| AC-13 | 并行锁任务级文件锁 | 3-develop.md .lock 检查 + .lock 模板 | PASS |
| AC-14 | 锁的创建与释放 | 3-develop.md 步骤6锁创建 + 步骤11锁释放 | PASS |
| AC-15 | 同任务互斥 | 3-develop.md 含"非当前任务→阻止" | PASS |

**验收结果：17/17 AC PASS**

## 健康评分

**综合评分：83.4 / 100（B级）**

| 维度 | 分数 | 权重 |
|------|------|------|
| AC 通过率 | 100 | 22% |
| 测试覆盖 | 50 | 18% |
| 评审效率 | 100 | 13% |
| 代码质量 | 80 | 13% |
| 边界卫生 | 100 | 13% |
| 文档完备 | 50 | 10% |
| 资源效率 | 100 | 11% |

## 范围排除确认

- 未实现自动拆分逻辑 ✓（仍由产品经理人工拆分）
- 未实现 change 间自动依赖检测 ✓（人工标注）
- 未实现跨进程分布式锁 ✓（限定文件锁）

## 非功能需求确认

- PIPELINE.md 读写 < 100ms ✓（纯文件操作）
- 不引入外部依赖 ✓
- 无 PIPELINE 时完全不影响 ✓

## 进化分析

- evolution_signal: should_reflect=false（无强信号）
- 跳过进化反思

## 验收签字

**产品经理**：✅ 17/17 AC 全通过，验收线满足
**项目经理**：✅ 5 任务按时完成，1 Major bug 已修复，0 严重项残留
