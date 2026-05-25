# DESIGN — autoresearch-borrow

## 0. 技术选定
不需要新技术栈。所有改动在现有 Markdown 技能文件内完成。

## 1. 变更点地图

| 机制 | 文件 | 变更位置 | 变更内容 |
|------|------|---------|---------|
| Guard | SKILL.md | 配置表 | 新增 `guard_enabled`/`guard_timeout` |
| Guard | task-artifacts.md | TASK 模板 | 新增 `<guard>` 可选字段 |
| Guard | 3-develop.md | 步骤 9-10 之间 | 新增 Guard 执行步骤 |
| Git as Memory | SKILL.md | 配置表 | 新增 `git_memory_depth` |
| Git as Memory | special-flows.md | 回溯流程步骤 1-2 之间 | 新增 git log/diff 读取 |
| Git as Memory | 3-develop.md | 精炼环 | 边界卫生增加 git 历史检查 |
| Plateau | SKILL.md | 配置表 | 新增 `stagnation_patience` |
| Plateau | 3-develop.md | 自调节机制区域 | 新增停滞检测逻辑 |
| Plateau | 4-test.md | 自调节机制区域 | 新增停滞告警 |
| TSV 日志 | SKILL.md | 配置表 | 新增 `iteration_log` |
| TSV 日志 | 3-develop.md | 步骤 14 附近 | 新增 TSV 追加步骤 |
| TSV 日志 | 4-test.md | 步骤 8-9 之间 | 新增 TSV 追加步骤 |

## 2. Guard 执行流程
```
task 完成 → verify 通过 → 精炼环 → Guard 执行 → 提交
                               ↓           ↓
                          失败→回滚    超时→告警继续
```

## 3. Plateau 行为规格

**3-开发阶段**：
- 维护计数器 `consecutive_failures`（STATE.md 阶段进度中记录）
- task verify 或 Guard 失败 → counter += 1
- task 成功 → counter 重置为 0
- counter >= stagnation_patience → 暂停，输出升级报告：
  ```
  ⚠️ Plateau 检测：连续 {N} 个 task 未能通过验证
  已尝试方法：{列出失败 task 的 action 摘要}
  推荐方向：{基于 git log 分析失败模式，建议 2-3 个替代方向}
  ```
- 用户选择：(a) 调整策略后继续 (b) 跳过当前 task (c) 中断

**4-测试阶段**：
- 在现有 test_rounds 循环内追踪：连续轮次 Critical/High 数未减少
- 连续 stagnation_patience 轮无改善 → 输出告警（不暂停，仅建议）

## 4. TSV 格式与容错
```
timestamp\tstage\ttask_id\taction\tstatus\tmetric\tdescription
```
- status: pass / fail / timeout / skip
- 追加模式，不修改历史行
- 首次写入：文件不存在时先写入表头行再追加数据行
- 追加失败：降级告警（不影响 task 流程），记录到 SUMMARY.md

## 5. Git as Memory 重叠判定
精炼环「已回滚方案重叠」判定规则：
- 提取最近 5 个 commit 消息中含 `Revert` 或 `回滚` 的条目
- 提取被回滚方案的 commit message（从 Revert 消息解析，如 `Revert "experiment(api): add caching"`）
- 比对当前 task 的 action 描述与被回滚方案的消息关键词交集
- 关键词交集 ≥ 2 个（非停用词）→ 判定为重叠

## 6. ADR

### ADR-001 Guard 位置在 verify 之后
- 背景：Guard 可放在 verify 之前或之后
- 选项：A. verify 前 / B. verify 后
- 决策：B（verify 后）
- 理由：verify 验证的是 task 功能正确性，Guard 验证的是无回归。先确认功能正确再检查回归，逻辑更清晰。Guard 失败时回滚的是已验证功能的改动，而非未验证的改动。

### ADR-002 TSV 而非 JSON Lines
- 背景：迭代日志需要机读格式
- 选项：A. TSV / B. JSON Lines / C. CSV
- 决策：A（TSV）
- 理由：TSV 最简单，无转义需求（description 中不会有 tab），grep/awk 可直接解析，无需解析器。JSON Lines 更结构化但增加了不必要的复杂度。

## 7. 风险
| 风险 | 概率 | 缓解 |
|------|------|------|
| Guard 字段缺失导致旧 TASK 不兼容 | 低 | guard 为可选，缺失跳过 |
| TSV 文件累积过大 | 低 | 归档时随 spec 一起清理 |
| Git log 读取耗时长 | 低 | 默认深度 20，可配置 |
| Guard 命令越权修改被守护文件 | 低 | 约束声明 guard 文件不在 write_files 内；精炼环边界卫生检查会捕获 |

## 8. 既有架构对齐
- 触碰模块：SKILL.md、references/stages/、references/artifacts/
- 禁动清单：路由逻辑、STATE 管理核心、闸门检查核心
- 沿用决策：精炼环结构、验证闭环模式
