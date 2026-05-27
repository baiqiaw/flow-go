# REQUIREMENT — token-optimize-p0-p2

## 用户原始输入
对 flow-go 进行 P0-P2 token 优化：基于 caveman 插件分析，优化 token 消耗，防止行为漂移，保证 Codex CLI 兼容。

## 问题陈述

### 痛点
1. **Token 浪费**：flow-go 8 阶段流程中约 30% token 消耗在礼貌用语、铺垫、重复解释上
2. **行为漂移**：长会话上下文压缩可能裁剪关键流程规则，导致 AI 遗忘阶段纪律
3. **安全风险**：压缩模式可能导致关键操作（部署、git push）描述过于简略，增加误操作风险
4. **子代理膨胀**：子代理冗长输出直接注入主上下文，消耗 token 预算

### 当前障碍
- SKILL.md 仅一次性注入，无 Per-Turn 强化
- 无输出风格分层控制
- 无子代理输出压缩契约
- 无可量化 token 度量

## 验收准则

### AC-1：分层输出模式
Given flow-go 处于任一阶段，When 系统按阶段映射表选择输出模式，Then AI 输出按对应级别压缩（normal/tight/caveman/ultra），压缩比达 60-70%。

### AC-2：Per-Turn 强化（Hook 路径）
Given Claude Code 环境配置了 SessionStart 和 UserPromptSubmit Hook，When 每轮用户输入，Then 系统注入当前阶段锚点口诀和输出模式，保持阶段纪律不漂移。

### AC-3：Per-Turn 强化（内联回退）
Given 非 Claude Code 环境（如 Codex CLI），When 加载 flow-go skill，Then SKILL.md 中的内联回退指令块在每轮用户输入时激活，行为与 Claude Code Hook 等价。

### AC-4：Auto-Clarity 安全边界
Given 当前处于压缩模式（tight/caveman/ultra），When 遇到安全审查、部署确认或不可逆操作，Then 自动切回 normal 模式完整输出，操作完成后恢复原模式。

### AC-5：子代理输出压缩
Given 主代理处于 caveman/ultra 模式，When 调度子代理（探索/审查），Then 子代理输出按压缩契约格式（≤15字说明/≤20字问题+修复），不输出完整句子。

### AC-6：Token 追踪
Given trace_collector.py 扩展了 token 追踪功能，When 记录 token 消耗数据，Then 可输出 per-stage token 汇总，支持 --estimate-tokens 启发式估算。

## 非功能需求
- Hook 响应时间 < 10ms（SessionStart）/ < 5ms（UserPromptSubmit）
- Hook 静默失败：所有 I/O 异常不阻塞会话
- 向后兼容：无 token 字段的旧 traces.jsonl 记录仍可读取
