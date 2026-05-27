# DESIGN — token-optimize-p0-p2

## Section 1: 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    flow-go 输出模式系统                    │
├─────────────────────────────────────────────────────────┤
│  SKILL.md (配置源)                                       │
│  ├── 第二步半: 输出模式定义 + 阶段映射                      │
│  ├── 平台检测 (CLAUDE_CONFIG_DIR)                         │
│  └── Per-Turn 强化指令块 (内联回退)                        │
├─────────────────────────────────────────────────────────┤
│  Hook 层 (Claude Code)                                   │
│  ├── SessionStart → flow-go-activate.js                  │
│  │   └── 读 terse-mode.md → 写旗标 → 注入规则到 stdout    │
│  └── UserPromptSubmit → flow-go-mode-tracker.js          │
│      └── 检测模式切换 → 发射 Per-Turn 强化                 │
├─────────────────────────────────────────────────────────┤
│  共享模块 (hooks/flow-go-config.js)                       │
│  ├── getDefaultMode() (ENV→配置→默认)                     │
│  ├── safeWriteFlag() (防符号链接, 原子写)                  │
│  ├── readFlag() (白名单校验, 大小上限)                     │
│  └── getStageAnchor() (阶段锚点口诀)                      │
├─────────────────────────────────────────────────────────┤
│  规则源 (references/terse-mode.md)                       │
│  ├── 4 级模式定义 (normal/tight/caveman/ultra)            │
│  ├── 阶段默认映射表                                       │
│  └── 安全自动退出条件                                     │
├─────────────────────────────────────────────────────────┤
│  子代理层                                                │
│  └── cross-review-matrix.md: 压缩输出契约                 │
│      ├── 探索子代理: path:line — symbol — ≤15字说明       │
│      └── 审查子代理: path:line 置信度% 维度: ≤20字修复    │
├─────────────────────────────────────────────────────────┤
│  度量层 (references/scripts/trace_collector.py)           │
│  ├── --estimate-tokens: len/4 启发式                     │
│  ├── --record-tokens: 记录到 traces.jsonl                │
│  └── --stage-summary: per-stage 汇总                     │
└─────────────────────────────────────────────────────────┘
```

## Section 2: 数据流

1. 会话启动 → SessionStart Hook → 读配置 → 写旗标 → 读 terse-mode.md → 输出规则文本到 stdout → Claude Code 注入为系统上下文
2. 每轮用户输入 → UserPromptSubmit Hook → stdin JSON → 检测模式切换指令/自然语言 → 更新旗标或发射 hookSpecificOutput → Claude Code 注入 additionalContext
3. 内联回退 → SKILL.md Per-Turn 指令块 → 等价于 Hook 的 additionalContext

## Section 3: API 设计

### 旗标文件格式
```json
{"mode": "normal", "stage": "3-开发", "updated": "2026-05-27T14:00:00+08:00"}
```
路径：`$CLAUDE_CONFIG_DIR/.flowgo-mode`（CLAUDE_CONFIG_DIR 不存在时回退 `~/.claude/.flowgo-mode`）

### 模式值
`normal` | `tight` | `caveman` | `ultra`

### 配置项
- `output_mode`：默认模式（默认 normal），在 references/configuration.md 和 SKILL.md 中定义
- `FLOWGO_DEFAULT_MODE` 环境变量覆盖配置文件

## Section 4: ADR

### ADR-001: 4 级分层模式
**决策**：采用 4 级输出模式（normal/tight/caveman/ultra），按阶段自动映射。
**替代方案**：2 级（开/关）— 太粗糙，无法平衡信息密度和安全性。
**权衡**：4 级增加配置复杂度，但提供更精确的控制粒度。

### ADR-002: Hook 双轨制 + 内联回退
**决策**：Claude Code 使用 Hook（SessionStart + UserPromptSubmit），其他平台使用 SKILL.md 内联回退指令块。
**替代方案**：仅 Hook — 不支持 Codex CLI 等平台。
**权衡**：双轨维护成本，但关键平台（Claude Code）获得最优体验，其他平台有降级方案。

### ADR-003: 代码块和技术术语保留
**决策**：所有压缩级别均保留代码块、错误原文、URL、技术术语不变。
**替代方案**：全局压缩 — 可能导致技术信息丢失。

### ADR-004: Token 追踪 — API 优先 + 启发式回退
**决策**：优先使用 API 返回的实际 token 数，不可用时使用 len(text)/4 启发式。
**替代方案**：tiktoken 精确计算 — 增加外部依赖，启发式误差 < 5% 可接受。

### ADR-005: 子代理压缩契约
**决策**：定义探索和审查子代理的压缩输出格式，主代理按需启用。
**替代方案**：子代理始终完整输出 — 浪费 token，与优化目标冲突。

## Section 4.5: 分层模式规则定义表

| 级别 | 删除项 | 保留项 | 输出格式 |
|------|--------|--------|---------|
| normal | 无 | 全部 | 完整自然语言 |
| tight | 礼貌用语/模糊修饰/冗余前缀/过度铺垫/冗长转折 | 完整句子结构/技术实质 | 简短句子 |
| caveman | tight全部 + 冠词/填充词/寒暄/长同义词 | 技术实质/代码/URL | `[对象] [动作] [原因]。[下一步]。` |
| ultra | caveman全部 + 连接词/主语/介词 | 技术标识符/数字 | 箭头因果 + 单字表达 |

## Section 5: 安全边界

Auto-Clarity 触发条件：
1. 不可逆操作确认（git push --force / 数据库迁移 / 权限变更）
2. 安全审查步骤（5-审查 HARD-GATE）
3. 部署操作（6-部署阶段）
4. 用户困惑检测（连续 2 次提问同一问题）
5. 错误发生（命令 exit != 0）

## Section 6: 验证策略

- 回归测试：27 个 pytest 测试全部通过
- Hook 测试：手动验证 SessionStart 输出 + UserPromptSubmit 模式切换
- Codex CLI：手动验证内联回退行为等价性
- Token 压缩比：对比优化前后完整流程 token 消耗

## Section 7: 验证假设

| # | 假设 | 推翻信号 |
|---|------|---------|
| 1 | 分层输出模式降低 token 消耗 60-70% | 压缩比 < 20% |
| 2 | Per-Turn 强化不干扰阶段行为指令 | 任意 eval 场景失败 |
| 3 | Codex CLI 内联回退与 Hook 等效 | Codex 行为与 Claude Code 显著偏离 |
| 4 | len(text)/4 启发式与 tiktoken 误差 < 5% | 偏差 > 10% |
