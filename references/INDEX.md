# INDEX.md — references

## 边界描述

flow-go 的参考文档。SKILL.md 路由后按阶段名/工件名加载对应文件，禁止整读。

## 子文件夹

### stages/ — 阶段执行指南
| 文件 | 阶段 | 角色 | 行数 |
|------|------|------|------|
| `0-requirement.md` | 0-需求 | 产品经理 | ~35 |
| `1-design.md` | 1-设计 | 技术经理 | ~35 |
| `2-task.md` | 2-任务 | 项目经理 | ~35 |
| `3-develop.md` | 3-开发 | 开发员 | ~50 |
| `4-test.md` | 4-测试 | 测试员 | ~40 |
| `5-review.md` | 5-审查 | 技术经理 | ~40 |
| `6-deploy.md` | 6-部署 | 运维 | ~30 |
| `7-acceptance.md` | 7-验收 | 产品经理+项目经理 | ~30 |
| `special-flows.md` | 热修/归档/废弃/回溯/归档维护 | 按流程 | ~190 |

### artifacts/ — 工件模板
| 文件 | 包含工件 | 行数 |
|------|---------|------|
| `meta-artifacts.md` | STATE.md / CONTEXT.md / LESSONS.md / ARCHIVE-INDEX.md | ~110 |
| `spec-artifacts.md` | CHANGE.md / REQUIREMENT.md / DESIGN.md / ARCHIVE.md | ~125 |
| `task-artifacts.md` | TASK.md / SUMMARY.md / PROGRESS.md | ~120 |
| `quality-artifacts.md` | TEST.md / REVIEW.md / 交叉评审报告 | ~150 |
| `deploy-artifacts.md` | DEPLOY.md / UAT.md / ABANDONED.md | ~110 |

### artifacts/examples/ — 工件标准示例
| 文件 | 展示工件 | 行数 |
|------|---------|------|
| `requirement-example.md` | REQUIREMENT.md 好工件标准 | ~60 |
| `task-example.md` | TASK.md 好工件标准 | ~70 |
| `e2e-scenario.md` | 端到端场景演练（8 阶段完整流程 + 异常场景） | ~220 |
| `summary-example.md` | SUMMARY.md 好工件标准 | ~90 |

## 根级文件

- `handoff-protocols.md` — 阶段交接协议（7 组 FROM/TO 上下文转移清单，~100 行）
- `anti-patterns.md` — 阶段反面模式（8 阶段各 4-5 条 Anti-Pattern 表，~130 行）
- `health-dimensions.md` — 健康评分维度说明（7 维权重 + RAG 判定 + 趋势规则，~50 行）
- `decision-framework.md` — 角色协作决策树（6 角色 × 5 场景升级指引，~70 行）
- `prioritization-quickref.md` — 优先级框架速查（MoSCoW / ICE / RICE / WSJF / MCDA + 自动推荐）
- `routing-diagram.md` — 路由决策 DOT 流程图（按需加载，~80 行）
- `cross-review-matrix.md` — 交叉评审规范（3 套 6 维矩阵定义 + 子代理 prompt 模板 + 失败处理策略）
- `path-modes.md` — 路径模式定义（完整/增量/最短三种模式的闸门适配和工件差异）
- `sync-workflow.md` — 知识库同步工作流（全量/增量/受作用域三种模式的执行步骤和自检清单，~190 行）
- `agent-paths.md` — 各 Agent 平台的记忆与配置路径速查（~70 行）
- `sync-matrix.md` — 变更类型到需同步文件的映射表（~55 行）

## scripts/

**依赖**：所有脚本仅使用 Python 标准库（argparse/json/os/re/sys/subprocess/datetime/pathlib/random/collections），无第三方依赖。Python >= 3.8。

- `health_scorer.py` — 7 维健康评分 + 趋势追踪（health-history.jsonl）+ 趋势分析/自动分诊
- `risk_analyzer.py` — 风险矩阵（概率×影响，1-9 分）+ EMV 量化 + 三点估算 + 应对策略推荐
- `task_estimator.py` — 蒙特卡洛工时预测（5000 次迭代，置信区间）
- `lessons_indexer.py` — LESSONS 索引器（JSONL 生成 + 关键词搜索）
- `evolution_signal.py` — 进化信号检测器（强/中信号 + 归因标签 + Cheap Gate）
- `evolution_reflect.py` — 进化反思器（信号→假设→签名去重→目标路由→风险决策 + 顿悟机制 + 策略捕获 context 扩展）
- `evolution_gate.py` — 三重门控系统（约束门+回归门+安全门）
- `complexity_classifier.py` — 复杂度分级器（多信号加权评分，LITE/STANDARD/HEAVY）
- `gate_check.py` — 闸门检查脚本（工件检查 + blast radius 双模式）
- `bitter_pill_audit.py` — 苦丸审计脚本（规则文本扫描 + KEEP/REVIEW/CANDIDATE 分类）
- `completion_forecaster.py` — 完成率预测器（基于历史数据线性趋势预测 + 置信区间 + 任务完成预测）
