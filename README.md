# Flow-Go

6 角色 × 8 阶段的 AI 辅助开发流程编排框架。为 AI 编程工具提供结构化的软件开发生命周期管理——从需求到验收，每一步都有明确的角色、闸门和工件。

**解决的问题**：AI 编程工具擅长写代码，但缺乏项目级的流程约束。flow-go 通过状态机驱动 + 闸门检查 + 角色分工，确保每次变更都经过完整的质量流程，避免跳步、遗漏和幻觉。

**核心理念**：
- 状态驱动，不是对话驱动——`STATE.md` 是唯一状态源
- 闸门不跳步——每个阶段有前置条件，不满足就停下
- 角色有红线——产品经理不写代码，开发员不改需求

## 流程

```
[0-需求] → [1-设计] → [2-任务] → [3-开发] → [4-测试] → [5-审查] → [6-部署] → [7-验收]
  产品经理    技术经理    项目经理    开发员     测试员    技术经理    运维    产品经理+项目经理
```

特殊流程：`归档` / `废弃` / `热修` / `回溯` / `整理` / `归档维护` / `进化分析`

## 安装

### 前置条件

- Git
- Python 3.8+（辅助脚本）
- 支持的 AI 编程工具（见下方各工具安装方式）

### Claude Code

```bash
# 符号链接到 Claude Code skills 目录
ln -s /path/to/flow-go ~/.claude/skills/flow-go
```

在项目目录中输入 `flow-go` 即可触发。

### Codex CLI

```bash
# 方式 1：通过 .codex-plugin 自动识别
# 在项目根目录创建 .codex-plugin/plugin.json，指向 flow-go

# 方式 2：放入全局插件目录
ln -s /path/to/flow-go ~/.codex/plugins/flow-go
```

### Trae

```bash
# 创建符号链接到 .trae/skills/ 目录
mkdir -p .trae/skills
ln -s /path/to/flow-go .trae/skills/flow-go
```

### Cursor

```bash
# 创建符号链接到 .cursor/rules/ 目录
mkdir -p .cursor/rules
ln -s /path/to/flow-go/SKILL.md .cursor/rules/flow-go.mdc
```

### Windsurf

```bash
# 创建符号链接到 .windsurf/rules/ 目录
mkdir -p .windsurf/rules
ln -s /path/to/flow-go/SKILL.md .windsurf/rules/flow-go.md
```

### Cline

在 Cline 的 Custom Instructions 中粘贴 flow-go 的 SKILL.md 内容，或将项目克隆到工作区中。

### OpenCode

```bash
# 方式 1：使用 .opencode/skills/（自动发现）
mkdir -p .opencode/skills
ln -s /path/to/flow-go .opencode/skills/flow-go

# 方式 2：兼容 Claude Code 路径（自动发现）
# 已有 ~/.claude/skills/flow-go 链接时 OpenCode 会自动识别
```

### OpenClaw

```bash
# 放入 OpenClaw skills 目录
ln -s /path/to/flow-go ~/.openclaw/skills/flow-go
```

### 更新

```bash
cd /path/to/flow-go
git pull
```

符号链接无需更新，自动指向最新代码。

## 使用

### 快速开始

在项目目录中，向 AI 编程工具输入：

- **`flow-go`** 或 **`go`** — 自动路由到当前阶段下一步
- **阶段关键词**（`需求`、`设计`、`开发`、`测试`、`审查`、`部署`、`验收`）— 直接跳转到指定阶段
- **描述新需求** — 自动进入 0-需求阶段并生成 change-id

### 常用命令

| 输入 | 说明 |
|------|------|
| `go` / `下一步` | 路由到当前阶段下一步 |
| `需求 <描述>` | 开始新需求 |
| `开发` / `测试` / `审查` | 跳转到指定阶段 |
| `归档` / `收工` | 归档当前变更 |
| `继续` / `接着上次` | 恢复中断的工作 |
| `保存` | 保存当前进度 |

### 配置

在项目根目录创建 `.flowgo-config` 或用户目录 `~/.flowgo-config`：

```yaml
test_rounds: 3              # 测试阶段单轮修复上限
max_files_per_task: 10      # 单任务改动文件上限
auto_sync: true             # 决策信号自动触发知识库同步
priority_framework: MoSCoW  # 优先级框架
explain_level: default      # 解释详细度（default / terse）
evolution_mode: auto        # 进化分析模式（auto / off）
complexity_threshold: 5     # blast-radius 文件数阈值
bitter_pill_auto: true      # 归档后自动触发苦丸审计
preflight_check: true       # 任务阶段启用预检环
context_budget_mode: auto   # 上下文预算模式（auto / manual / off）
```

## 项目结构

```
SKILL.md                          # 主 skill 定义（路由 + 状态机 + 规则）
INDEX.md                          # 边界描述与文件索引
references/
  stages/                         # 8 个阶段 + 特殊流程的执行步骤
    0-requirement.md ~ 7-acceptance.md
    special-flows.md
  artifacts/                      # 工件模板（CHANGE/REQUIREMENT/DESIGN/TASK/TEST/REVIEW 等）
  scripts/                        # Python 辅助脚本
    complexity_classifier.py      # 复杂度自动分级
    gate_check.py                 # 闸门检查
    health_scorer.py              # 健康评分
    risk_analyzer.py              # 风险分析
    task_estimator.py             # 任务估算
    evolution_signal.py           # 进化信号检测
    evolution_reflect.py          # 进化反思
    evolution_gate.py             # 进化触发门控
    bitter_pill_audit.py          # 苦丸审计（规则自审计）
    lessons_indexer.py            # 教训索引
  sync-workflow.md                # 知识库同步工作流
  sync-matrix.md                  # 决策→同步变更映射
  handoff-protocols.md            # 阶段交接协议
  cross-review-matrix.md          # 交叉评审矩阵
  decision-framework.md           # 决策框架
  anti-patterns.md                # 反模式清单
  routing-diagram.md              # 路由决策流程图
  agent-paths.md                  # 代理路径速查
  path-modes.md                   # 路径模式说明
  health-dimensions.md            # 健康维度定义
  prioritization-quickref.md      # 优先级框架速查
evals/
  evals.json                      # 评估配置
```

## 核心机制

- **状态驱动**：`STATE.md`（项目根目录）维护活跃 Change、当前阶段、当前任务
- **闸门检查**：每个阶段有前置条件，不满足则停下引导补齐
- **角色红线**：每个角色有明确禁止事项（如开发员不可改需求、测试员不可自己修代码）
- **按需加载**：每个阶段仅加载对应的 stage + artifact 文件，不整读
- **复杂度分级**：LITE / STANDARD / HEAVY，影响闸门严格程度
- **知识库同步**：决策信号自动触发受作用域同步，验收后全量同步
- **进化分析**：归档后自动检测进化信号，健康评分驱动 CAPTURE/FIX 双路径

## License

MIT
