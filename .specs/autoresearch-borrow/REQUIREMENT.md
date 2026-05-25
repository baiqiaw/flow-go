# REQUIREMENT — autoresearch-borrow

## 用户故事
作为 flow-go 用户，我希望开发阶段有实时回归防护、回溯时能利用 git 历史、停滞时自动告警、迭代记录可机读，以便减少返工、提高跨会话恢复精准度、避免在死胡同浪费 token。

## 验收准则（BDD）

### AC-1 Guard 机制
**Given**: 一个 TASK.md 中定义了 `guard: <shell-command>` 字段
**When**: 3-开发阶段完成一个 task 的代码编写并通过精炼环
**Then**: 自动运行 guard 命令；通过则继续，失败则回滚该 task 改动并记录到 SUMMARY.md

### AC-2 Guard 配置项
**Given**: flow-go 配置文件中有 `guard_timeout` 和 `guard_enabled` 配置项
**When**: 用户在 .flowgo-config 中设置 guard_timeout=60
**Then**: guard 命令执行超过 60 秒自动终止并视为通过（不阻塞，仅告警）

### AC-3 Git as Memory — 回溯增强
**Given**: 一个 change 因中断而需要回溯恢复
**When**: 用户说「继续/接着上次/resume」触发回溯流程
**Then**: 自动读取 `git log --oneline -20` 和最近 3 个 commit 的 diff 摘要，将关键信息注入会话上下文

### AC-4 Git as Memory — 精炼环集成
**Given**: 3-开发阶段精炼环正在执行
**When**: 检查「边界卫生」项
**Then**: 额外检查 git log 中最近 5 个 commit，识别已回滚的方案并避免重复

### AC-5 Plateau 检测 — 开发停滞
**Given**: 3-开发阶段正在执行 task 序列
**When**: 连续 N 个 task（默认 3，配置项 stagnation_patience）未能通过验证
**Then**: 输出升级报告（已尝试方法 → 推荐替代方向），请用户决定是否调整策略

### AC-6 Plateau 检测 — 测试停滞
**Given**: 4-测试阶段正在执行修复循环
**When**: 连续 N 轮修复（默认 test_rounds）未能减少错误数
**Then**: 输出停滞告警，建议用户调整测试策略或扩大 scope

### AC-7 结构化迭代日志
**Given**: 一个 change 的 3-开发或 4-测试阶段正在执行
**When**: 每个 task 或测试轮次完成
**Then**: 将结果追加到 `.specs/<id>/iterations.tsv`（字段：timestamp / stage / task_id / action / status / metric / description）

### AC-8 迭代日志消费
**Given**: iterations.tsv 文件已存在
**When**: 飞轮分析或进化分析读取该文件
**Then**: 能直接解析 TSV 格式获取结构化数据，无需解析 Markdown

## 非功能需求
- 性能：guard 命令执行不超过配置的超时时间
- 安全：guard 命令不能修改被守护的文件（如测试文件）
- 兼容：现有无 guard 字段的 TASK.md 向后兼容（guard 为可选）

## Out of Scope（范围排除）
- 多维度测试矩阵（12 维度）
- 批量问答优化
- Chain 机制
- 噪声处理
- 路由逻辑或状态管理核心修改

## Principles（设计约束原则）
- 所有新增机制必须向后兼容（现有流程不受影响）
- 不引入新的外部依赖
- 新增配置项必须在 SKILL.md 的配置表中声明

## Key Decisions（关键决策记录）
| 决策 | 理由 | 影响 |
|------|------|------|
| Guard 为可选字段 | 向后兼容现有 TASK.md | 无 guard 的 task 跳过检查 |
| Plateau 默认 patience=3 | 平衡灵敏度和误报 | 可通过配置调整 |
| iterations.tsv 为追加模式 | 不修改历史记录 | 飞轮分析可直接消费 |
| Git as Memory 读取深度 20 | 与 autoresearch 保持一致 | 可通过配置调整 |

## 术语表
| 术语 | 含义 |
|------|------|
| Guard | 开发过程中运行的回归防护命令，确保改动不破坏已有功能 |
| Plateau | 连续多次迭代无改善的状态，提示需要策略调整 |
| Git as Memory | 利用 git 历史记录作为 AI Agent 的长期记忆 |
| iterations.tsv | 结构化迭代日志文件，TSV 格式记录每次 task/测试结果 |
