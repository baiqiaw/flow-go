# Flow-Go

6 角色 × 8 阶段 AI 开发流程编排 skill。输入 `go` 即可自动路由到下一步。

## 流程

```
[0-需求] → [1-设计] → [2-任务] → [3-开发] → [4-测试] → [5-审查] → [6-部署] → [7-验收]
  产品经理    技术经理    项目经理    开发员     测试员    技术经理    运维    产品经理+项目经理
```

特殊流程：`归档` / `废弃` / `热修` / `回溯` / `整理` / `归档维护` / `进化分析`

## 使用

在 Claude Code / Codex CLI / OpenCode / OpenClaw 中输入：

- `go` — 自动路由到当前阶段下一步
- 阶段关键词（`需求`、`设计`、`开发`、`测试` 等）— 直接跳转
- 描述新需求 — 自动进入 0-需求阶段

### 配置

在项目根目录创建 `.flowgo-config` 或用户目录 `~/.flowgo-config`：

```yaml
test_rounds: 3
max_files_per_task: 10
auto_sync: true
priority_framework: MoSCoW
explain_level: default
evolution_mode: auto
complexity_threshold: 5
bitter_pill_auto: true
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

## 安装

将本项目链接到 Claude Code 的 skills 目录：

```bash
ln -s /path/to/flow-go ~/.claude/skills/flow-go
```

Codex CLI 通过 `.claude-plugin/plugin.json` 自动识别。

## License

MIT
