# REQUIREMENT — skill-evolver-optimization

## 用户故事
作为 flow-go 维护者，我希望流程具备自进化闭环能力，以便每次 Change 的经验能自动驱动下一次改进，而不需要手动运行进化分析。

## 验收准则（BDD）

### AC-1 第 5 维效率门控
**Given**: gate_check.py 以 quality-gate 模式运行
**When**: 执行全量质量门控检查
**Then**: 返回 5 个维度（quality, scope, security, regression, efficiency），全部 AND 逻辑判定 passed

### AC-2 效率维度计算
**Given**: specs 目录下存在 *-SUMMARY.md 且含 AC 通过信息
**When**: 检查效率维度
**Then**: 计算 AC 通过数（从 TEST.md 或 *-SUMMARY.md 提取） / (代码行数/100，代码行数来源为 git diff --stat 变更文件的总 +lines），比值 ≥ 阈值时 passed=true，< 阈值时 passed=false 并输出具体比值

### AC-3 无代码变更时的效率判定
**Given**: specs 目录下存在 *-SUMMARY.md 但 git diff 无代码改动
**When**: 检查效率维度
**Then**: passed=true（纯文档/配置变更不判效率）

### AC-4 L1 快速门卫模式
**Given**: gate_check.py 以 --mode l1-guard 运行
**When**: 执行 L1 快速检查
**Then**: 仅执行安全扫描 + blast radius + SKILL.md 结构检查（不跑 L2 全量评测），秒级返回

### AC-5 L3 条件触发判定
**Given**: gate_check.py 以 --mode quality-gate 运行
**When**: 同时传入 --enable-l3 参数且 specs_dir 的上级目录存在 traces.jsonl
**Then**: 额外执行跨 Change 回归检查（读 traces.jsonl 最近 3 条记录，比对 gate_blocks 是否有新阻断）

### AC-6 进化信号自动写入 LESSONS
**Given**: 进化信号检测输出包含 strong_signals
**When**: evolution_signal.py 增加 --write-lessons 参数
**Then**: 信号自动格式化为 LESSONS.md 条目追加到"待改进领域"章节，格式为：`| {归因标签} | {信号描述} | {改进建议} |`，每条含归因标签 + 建议

### AC-7 开发阶段前置提醒
**Given**: 归档流程已完成进化信号写入 LESSONS.md
**When**: 下次进入 3-开发阶段
**Then**: 自动 grep LESSONS.md 中与当前 change 类型匹配的"待改进领域"条目，输出前置提醒

### AC-8 auto-verify 可选模式
**Given**: 3-开发阶段配置 auto_verify=true（在 .flowgo-config 中）
**When**: 开发员完成一个子任务
**Then**: 自动运行 gate_check.py --mode l1-guard，通过则继续，失败则输出失败项 + 建议 git stash

### AC-9 优先级路由输出
**Given**: evolution_reflect.py 处理信号生成假设
**When**: 输出结果中
**Then**: 包含 priority_ranking 字段，按 6 级优先级排序（1=修崩溃→2=利用成功→3=攻克持久失败→4=探索新方向→5=简化→6=激进变异）

### AC-10 优先级路由证据要求
**Given**: evolution_reflect.py 生成 priority_ranking
**When**: 优先级 1-3 的条目
**Then**: 每条必须包含 trace_evidence 字段（引用具体信号证据），无证据的条目优先级降为 4+

## 非功能需求
- 性能：L1 模式 < 5 秒，L2 模式 < 30 秒
- 安全：不引入新的外部依赖
- 兼容：现有 gate_check.py CLI 参数全部向后兼容
- token 效率：新增文件遵循 SRP + 渐进式披露，单个文件 ≤ 200 行，按需加载

## Out of Scope（范围排除）
- holdout/训练集数据分离
- SKILL.md 主文件路由改动
- 自动 git revert（仅建议 git stash）

## Principles（设计约束原则）
- 文件单一职责：每个文件一个清晰职责，方便 AI agent 按需读取
- 渐进式披露：只加载当前操作需要的文件，减少 token 占用
- CLI 参数向后兼容（新增可选参数，不修改已有参数语义）
- 遵循现有脚本风格（纯 Python 标准库、argparse CLI、JSON 输出）

## Key Decisions（关键决策记录）
| 决策 | 理由 | 影响 |
|------|------|------|
| 效率维度需要量化阈值 | 量化投入产出比，防止低效大改动通过门控 | gate_check.py 需新增效率计算，具体阈值在设计中确定 |
| 评测采用分层策略（快速/全量/条件触发） | 降低每轮检查成本，贵检查仅在条件触发时运行 | gate_check.py 需支持多模式 |
| 进化改进建议按优先级排序 | 确保最重要的改进先被处理 | evolution_reflect.py 输出格式需扩展 |
| auto-verify 默认关闭 | 自动化需要验证期，先 opt-in 再考虑 opt-out | .flowgo-config 新增配置项 |

## 术语表
| 术语 | 含义 |
|------|------|
| L1 快速门卫 | 秒级纯程序检查（安全扫描 + blast radius + 结构检查） |
| L2 全量评测 | 分钟级门控（4+1 维 AND） |
| L3 条件触发 | 跨 Change 回归检查，仅在特定条件时运行 |
| 效率维度 | AC 通过数 / (代码行数/100) 的比值，衡量改动投入产出比 |
| 优先级路由 | 按 6 级优先级排序进化改进建议，确保最重要的先被处理 |
