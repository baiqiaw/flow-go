# DESIGN — skill-evolver-optimization

## 0. 技术栈选定
| 候选 | 优点 | 缺点 | 推荐 |
|------|------|------|------|
| A. 纯 Python stdlib，按 SRP 拆分模块 | 零新依赖，SRP + 渐进式披露减少 token | 多文件需维护导入关系 | ★ 首选 |
| B. 单文件扩展 | 改动最少 | 500+ 行，AI agent 每次全文加载浪费 token | 排除 |
| C. 引入 click/外部库 | CLI 体验更好 | 违反"不引入新依赖"约束 | 排除 |

最终选择：A。理由：SRP 拆分使 AI agent 按需加载（3-开发只读 gate_l1.py ~60 行，不加载 L2/L3），token 效率最优。

## 1. 架构图

```
references/scripts/
├── gate_check.py          ← CLI 入口，瘦调度器（≤80 行）
│   --mode l1-guard        → gate_l1.py
│   --mode quality-gate    → gate_l2.py [+ gate_l3.py if --enable-l3]
│   --mode blast-radius    → gate_blast.py
│   --stage N              → gate_artifacts.py
│
├── gate_artifacts.py      ← 工件检查（现有 check_artifacts 提取）
├── gate_blast.py          ← blast radius 检查（现有 check_blast_radius 提取）
├── gate_l1.py             ← L1 快速门卫（安全+blast+结构，AC-4）
├── gate_l2.py             ← L2 全量评测，5 维 AND（AC-1）
│   ├─ _quality()          ← 现有 _check_quality_dimension
│   ├─ _scope()            ← 现有 _check_scope_dimension
│   ├─ _security()         ← 现有 _check_security_dimension
│   ├─ _regression()       ← 现有 _check_regression_dimension
│   └─ _efficiency()       ← 新增（AC-2/3）
├── gate_l3.py             ← L3 跨 Change 回归（AC-5，按需加载）
└── gate_dimensions.py     ← 共享常量：DANGEROUS_PATTERNS + 阈值

进化闭环链路（渐进式披露）：
references/scripts/
├── evolution_signal.py    ← 信号检测入口（瘦调度）
│   --write-lessons        → lessons_writer.py（AC-6）
│
├── lessons_writer.py      ← LESSONS.md 追加（AC-6，仅归档时加载）
└── evolution_reflect.py   ← 反思器，扩展输出 priority_ranking（AC-9/10）

references/stages/
├── 3-develop.md           ← 增加：入口处 grep LESSONS.md（AC-7）
│                          ← 增加：auto-verify 调用 gate_l1.py（AC-8）
└── special-flows.md       ← 增加：归档时调用 evolution_signal.py --write-lessons
```

## 2. 数据流

### L1 快速门卫（秒级）
```
gate_check.py --mode l1-guard --specs-dir .specs/xxx --project-dir .
    │
    ├─→ gate_l1.py
    │     ├─→ gate_dimensions.py (读 DANGEROUS_PATTERNS)
    │     │     → _security(): 扫描 specs 目录 .md 文件
    │     ├─→ gate_blast.py
    │     │     → git diff --name-only → 统计文件数
    │     └─→ _structure(): 检查 SKILL.md 结构
    │
    └─→ JSON {passed, dimensions: {security, blast, structure}}
```

### L2 全量评测（分钟级）
```
gate_check.py --mode quality-gate --specs-dir .specs/xxx --project-dir .
    │
    ├─→ gate_l2.py
    │     ├─→ _quality(): 读 *-SUMMARY.md 提取 verify 通过率
    │     ├─→ _scope(): 读 TASK.md write_files + git diff --name-only 比对
    │     ├─→ _security(): 同 L1
    │     ├─→ _regression(): 读 TEST.md 检查回归关键词
    │     └─→ _efficiency():
    │           ├─ 读 TEST.md 提取 AC 通过数（正则: "AC-\d+.*PASS"）
    │           ├─ git diff --stat 提取总 +lines
    │           ├─ 计算 ratio = ac_passed / (lines/100)
    │           └─ git diff 无改动 → passed=true
    │
    ├─→ [if --enable-l3]
    │     gate_l3.py
    │       → 读 .specs/traces.jsonl 最近 3 条
    │       → 比对 gate_blocks 是否有新阻断维度
    │
    └─→ JSON {passed, dimensions: {5+1}, l3: {...}}
```

### 进化闭环（归档时触发）
```
归档流程 (special-flows.md)
    │
    ├─→ evolution_signal.py --specs-dir .specs/xxx --write-lessons
    │     ├─→ detect() 提取信号（现有逻辑）
    │     └─→ lessons_writer.py（按需加载）
    │           ├─ 读 .specs/LESSONS.md
    │           ├─ 找到 "## 待改进领域" 章节
    │           └─ 追加: | 归因标签 | 信号描述 | 改进建议 |

3-开发阶段入口
    │
    ├─→ grep .specs/LESSONS.md 匹配当前 change 类型关键词 → 输出前置提醒
    │
    └─→ [if auto_verify=true]
          gate_check.py --mode l1-guard
          → PASS: 继续
          → FAIL: 输出失败项 + "建议 git stash 回滚"
```

## 3. API 设计

### gate_check.py 新增 CLI 参数
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--mode l1-guard` | choice | — | L1 快速门卫模式 |
| `--enable-l3` | flag | false | L3 条件触发（需配合 --mode quality-gate） |

### evolution_signal.py 新增 CLI 参数
| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `--write-lessons` | flag | false | 信号写入 LESSONS.md |

### 新增模块函数签名
| 模块 | 函数 | 输入 | 输出 |
|------|------|------|------|
| gate_l1.py | `check(specs_dir, project_dir)` | 路径 | `{passed, dimensions}` |
| gate_l2.py | `check(specs_dir, project_dir)` | 路径 | `{passed, dimensions}` |
| gate_l2 | `_efficiency(specs_dir, project_dir)` | 路径 | `{passed, ratio, detail}` |
| gate_l3.py | `check(specs_dir, traces_path)` | 路径 | `{passed, new_blocks}` |
| lessons_writer.py | `write(signals_payload, lessons_path)` | JSON+路径 | `{written, count}` |
| evolution_reflect.py | `reflect()` 扩展输出 | signals | +priority_ranking 字段 |

## 4. ADR

### ADR-001 文件拆分策略
- 背景：gate_check.py 290 行，加 L1/L2/L3/效率将膨胀到 500+ 行，AI agent 每次需全文加载
- 选项：A. 单文件扩展 / B. 按模式拆分为独立模块（SRP）
- 决策：B
- 理由：AI agent 按需加载——3-开发只读 gate_l1.py（~60 行），不加载 L2/L3。单文件扩展每次读 500 行浪费 token

### ADR-002 效率维度数据源
- 背景：效率 = AC 通过数 / 代码行数，需确定两个输入的数据源
- 选项：A. 从 TEST.md 解析 / B. 从 *-SUMMARY.md 解析 / C. 两者都尝试，优先 TEST.md
- 决策：C
- 理由：TEST.md 有结构化 AC 结果更准确；SUMMARY.md 作为 fallback 覆盖 TEST.md 不存在的场景

### ADR-003 L3 触发机制
- 背景：L3 跨 Change 回归检查成本高，需控制触发条件
- 选项：A. 自动检测 traces.jsonl 存在即触发 / B. 显式 --enable-l3 参数触发
- 决策：B
- 理由：显式参数让调用方明确知道 L3 会执行，避免隐含性能开销

### ADR-004 LESSONS.md 追加格式
- 背景：信号写入 LESSONS.md 需确定格式
- 选项：A. Markdown 表格行 / B. Markdown 列表项 / C. JSON 块
- 决策：A
- 理由：表格行结构化且可 grep，与现有 LESSONS.md 格式一致

### ADR-005 优先级路由排序依据
- 背景：evolution_reflect 输出需按 6 级优先级排序
- 选项：A. 归因频率 + 信号强度综合排序 / B. 纯信号强度 / C. 纯归因频率
- 决策：A
- 理由：高频率+高强度的信号最值得优先处理

### 优先级映射规则（AC-9）

| 优先级 | 名称 | 映射条件 | 示例 |
|--------|------|---------|------|
| P1 | 修崩溃 | 信号 type=gate_blocked 或 hotfix_trigger，且归因频率 ≥ 2 | 闸门连续 2 次 Change 被阻断 |
| P2 | 利用成功 | CAPTURE 模式产出的策略，健康评分 ≥ 8.5 | 高分 Change 的做法值得推广 |
| P3 | 攻克持久失败 | 同一 signature 在历史中出现 ≥ INSIGHT_THRESHOLD(3) 次 | 交叉评审反复未通过已出现 3+ 次 |
| P4 | 探索新方向 | 新出现的信号类型（无历史记录），或 P1-P3 无 trace_evidence 时降级 | 首次出现 role_violation |
| P5 | 简化 | blast_radius 或 similar_error 类信号，归因频率 = 1 | 单次 blast radius 触发 |
| P6 | 激进变异 | 用户显式要求的实验性改进，无历史数据支撑 | 用户主动提出的新方向 |

### trace_evidence 收集机制（AC-10）

P1-P3 条目必须包含 trace_evidence 字段，数据来源：
- P1：从 traces.jsonl 中该 change_id 的 gate_blocks 记录提取；或从 PROGRESS.md 中的闸门阻断记录提取
- P2：从 health-history.jsonl 最近一条记录提取 score 和 change_id
- P3：从历史假设 JSONL 中统计同 signature 出现次数的 change_id 列表

无 trace_evidence 时降级规则：该条目 priority 强制设为 P4，并在输出中标注 `"demoted": true, "demoted_from": "P1"`

## 5. 风险
| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 拆分 gate_check.py 后现有调用方找不到函数 | 中 | 高 | gate_check.py 保留原有函数签名，内部改为 `from gate_l1 import check` 委托调用；check_quality_gate() 签名不变 |
| 效率维度阈值不准（初始 0.5 过严或过松） | 中 | 低 | 阈值提取为 gate_dimensions.py 常量 EFFICIENCY_THRESHOLD，可配置；首版用 0.5，后续飞轮数据校准 |
| LESSONS.md 追加时"待改进领域"章节不存在 | 低 | 中 | lessons_writer.py 分两层处理：文件不存在 → 创建文件并写入基础模板（含"## 待改进领域"章节）；文件存在但章节不存在 → 追加章节标题后再追加条目 |
| L3 读 traces.jsonl 格式变化 | 低 | 中 | gate_l3.py 用 try/except 包裹 JSON 解析，解析失败返回 passed=true + detail 跳过而非阻断 |
| auto-verify L1 在大仓库超 5 秒 | 低 | 中 | blast radius 用 git diff --name-only（已很快）；3-develop.md 提示超时可手动跳过 |
| 优先级路由无 trace_evidence 的 P1-P3 条目 | 中 | 低 | AC-10 约束：无证据降级到 P4+，降级不阻断 |

## 6. 既有架构对齐

### 触碰模块
| 模块 | 改动类型 | 说明 |
|------|---------|------|
| references/scripts/gate_check.py | 重构 | 瘦身为 CLI 入口 + 委托调用，逻辑提取到子模块 |
| references/scripts/evolution_signal.py | 扩展 | CLI 新增 --write-lessons 参数，检测逻辑不变 |
| references/scripts/evolution_reflect.py | 扩展 | reflect() 输出新增 priority_ranking 字段 |
| references/stages/3-develop.md | 扩展 | 新增 LESSONS 前置提醒 + auto-verify 段落 |
| references/stages/special-flows.md | 扩展 | 归档流程新增 --write-lessons 调用步骤 |

### 新增模块
| 文件 | 职责 | 预估行数 |
|------|------|---------|
| references/scripts/gate_artifacts.py | 工件检查（现有逻辑提取） | ~60 |
| references/scripts/gate_blast.py | blast radius 检查（现有逻辑提取） | ~50 |
| references/scripts/gate_l1.py | L1 快速门卫 | ~70 |
| references/scripts/gate_l2.py | L2 全量 5 维评测 | ~130 |
| references/scripts/gate_l3.py | L3 跨 Change 回归 | ~60 |
| references/scripts/gate_dimensions.py | 共享常量 + 阈值 | ~30 |
| references/scripts/lessons_writer.py | LESSONS.md 追加 | ~50 |

### 禁动清单
- references/scripts/complexity_classifier.py — 不改
- references/scripts/risk_analyzer.py — 不改
- references/stages/0-requirement.md ~ 2-task.md — 不改
- references/artifacts/*.md — 不改
- SKILL.md — 不改（Scope 排除）

### 沿用决策
- CLI 入口保持 argparse + json.dumps 输出风格
- 信号检测沿用现有 STRONG_SIGNALS / MEDIUM_SIGNALS 字典结构
- 假设去重沿用 signature 机制
- 文件写入沿用 tmp + os.replace 原子模式
