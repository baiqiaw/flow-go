# Anti-Patterns — 阶段反面模式

> 每个阶段的常见错误模式。进入阶段时 grep 对应阶段，逐条检查产出是否命中。

---

## 0-需求 反面模式

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| [req-01-solution-as-requirement] 把解决方案当需求写 | "用 Redis 缓存"是方案不是需求，限制设计空间 | 只描述问题："查询延迟 > 500ms"，让设计阶段选方案 |
| [req-02-ac-positive-only] AC 仅覆盖正向路径 | 只写"用户点击提交成功"，缺少错误/边界/空值场景 | 补充：输入为空、权限不足、网络超时等边界 AC |
| [req-03-no-scope-exclusion] 没有范围排除 | 需求蔓延：做的时候越加越多，永远做不完 | 明确写"这次不做 X"，至少 1 条 |
| [req-04-hidden-assumptions] 隐性假设不声明 | "用户都用 Chrome"未写明，测试阶段才发现要兼容 IE | 影响面字段逐项填写，非功能需求给量化指标 |
| [req-05-multi-subsystem-no-split] 多子系统不拆分 | 一次改 5 个模块，任务拆解混乱，回归风险高 | 检测到 ≥3 模块 / ≥2 角色时建议拆分 change |
| [req-06-skip-clarification] **跳过澄清直接假设** | "用户已提供充分信息"跳过反问，基于猜测写需求 | 先做 4 维完整性评估，有 ❌ 必须提问，有 ⚠️ 必须确认 |

## 1-设计 反面模式

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| [des-01-no-alternatives] 技术栈选型无备选 | 只列一个方案，用户无法判断是否合理 | 列 3-5 候选，给首选+备选+排除理由 |
| [des-02-adr-no-comparison] ADR 无替代方案对比 | "决定用 X"无法追溯为什么不用 Y | 每条 ADR 必须有选项对比和排除理由 |
| [des-03-no-data-flow] 架构图缺数据流 | 只有模块框图，不描述数据怎么流动 | 补充请求从入口到存储的完整路径 |
| [des-04-ignore-existing-arch] 棕地项目忽略既有架构 | 新设计与旧系统冲突，开发阶段返工 | 必须有"既有架构对齐"：触碰模块/禁动清单/沿用决策 |
| [des-05-risk-no-mitigation] 风险清单无缓解方案 | "可能性能不好"列出但没有对策 | 每个风险必须有缓解方案，高风险量化解风险矩阵 |

## 2-任务 反面模式

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| [task-01-too-coarse] 任务粒度过粗 | "实现用户系统"跨多个 context，难以验证 | 每个任务 ≤ 1 context（通常 < 100 行代码） |
| [task-02-verify-not-executable] verify 不可执行 | "测试通过"不是 verify，无法自动判断 | verify 必须是可执行命令：`npm test -- xxx` / `pytest xxx` |
| [task-03-circular-deps] 依赖图有环 | T01 → T02 → T01，开发无法开始 | 画完依赖图后检查无环 |
| [task-04-missing-parallel] 遗漏并行标记 | 所有任务串行执行，浪费时间 | 无依赖的任务标 `[P]`，可并发执行 |
| [task-05-no-priority] 任务 > 3 个无优先级排序 | 所有任务等同看待，关键路径不清晰 | 用 MoSCoW/ICE/RICE 标注 priority，按优先级排序 |

## 3-开发 反面模式

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| [dev-01-skip-refactor] TDD 红绿环跳过 REFACTOR | 绿了就交，遗留坏味道和重复代码 | GREEN 后必须审视：可读性/重复/命名，在测试保护下整理 |
| [dev-02-cross-task-change] 跨任务改动 | 改了 TASK.md 未列的文件，引入未审查的变更 | diff 边界检查：`git diff --name-only` vs TASK 的 write_files |
| [dev-03-fake-verify] verify 输出造假 | 贴"通过"而非真实命令输出，掩盖失败 | 贴真实命令输出，未通过不标记完成 |
| [dev-04-reinvent-abstraction] 不沿用既有抽象 | 每次重写 HTTP 请求/日期格式化，增加维护成本 | grep 沿用既有抽象，找到就用 |
| [dev-05-vague-summary] SUMMARY 复制粘贴 DESIGN 描述 | "实现了用户模块"含糊不清，无法验证实际改动 | 写具体：改了哪个文件、哪个函数、怎么验证、哪些沿用 |
| [dev-06-bypass-unrelated-failures] 以"不是本次变更"绕过测试失败 | 非本次变更导致的测试失败被标记为"已有问题"跳过，遗留 bug | **任何测试失败都是阻塞项**，不区分失败来源，全部必须修复后才能继续 |
| [dev-07-complete-without-commit] 未提交代码就宣布开发完成 | 代码未 commit + SUMMARY 未写就说开发完成，下一阶段门禁拦截后回退 | 完成条件必须包含：verify 0 失败 + SUMMARY 完成 + 交叉评审 PASS + **代码已提交**，缺一不可 |

## 4-测试 反面模式

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| [test-01-derived-from-impl] 测试从实现派生 | 按代码写测试而非按 AC 写，实现改了测试就废了 | 每条 AC 映射到测试用例，AC 不变测试不变 |
| [test-02-weaken-failing] 删除/弱化失败用例 | 测试红了就改测试让变绿，掩盖真实 bug | 失败用例 → 报 bug → 开发修代码 → 重跑 |
| [test-03-skip-round-no-reason] 跳过轮次无理由 | "这轮不跑"但没有说明为什么，可能是偷懒 | 每个跳过的轮次必须有明确理由 |
| [test-04-no-metrics] 无量化数据 | "性能还行"无法回归对比 | 每轮报告量化：通过率、覆盖率、响应时间数值 |
| [test-05-matrix-by-file] 测试矩阵按文件组织而非按 AC | 测试只覆盖文件覆盖度，漏掉跨 AC 的集成场景 | 测试矩阵首列必须是 AC 编号，每条 AC 至少一个测试 |
| [test-06-no-retest-after-fix] **修复后不复测** | bug 修了就标记关闭，但没重跑发现它的测试确认修复有效 | 循环评审：修复 → 重测 → 仍有问题 → 再修 → 再测，直到 0 个 Critical/Major |

## 5-审查 反面模式

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| [rev-01-vague-report] 审查报告用语模糊 | "考虑改进"无法转化为行动，开发员不知道要改什么 | 每条发现必须包含：文件:行号 + 问题描述 + 建议改法 |
| [rev-02-detached-from-spec] 审查脱离 SPEC | 只看代码风格，不检查是否匹配需求/设计 | Spec 合规审查：实现是否覆盖每条 AC 和设计 |
| [rev-03-skip-security] 跳过安全扫描 | "这不涉及安全"而遗漏密钥/注入 | 每次必须跑 `git diff --staged \| grep -i "api_key\|token\|secret\|password"` |
| [rev-04-scope-mismatch] 审查范围与开发范围不一致 | 开发改了 8 个文件，审查只看了 3 个 | 以 `git diff --name-only` 全量清单为基础逐文件审查 |
| [rev-05-incomplete-coverage] 审查覆盖不全 | 只看最新改动，跳过跨任务交叉问题 | 速扫各 SUMMARY 交叉评审 + REVIEW.md，聚焦跨任务问题 |
| [rev-06-no-re-review] **严重项修复后不循环重审** | 修了就当完事，修复可能引入新问题（R2 变更传播） | 循环评审：修复 → 重审 → 仍有严重项 → 再修 → 再审，直到 0 严重项 |

## 6-部署 反面模式

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| [dep-01-skip-precheck] 跳过前置 4 问 | 本地工具也走部署流程，浪费时间 | 4 问逐项检查，有 ❌ 走替代路径 |
| [dep-02-no-rollback] 无回滚方案 | 部署失败后手足无措 | 部署前必须有回滚步骤和触发条件 |
| [dep-03-env-mismatch] CI/CD 配置与环境不一致 | staging 用 .env.staging，prod 没有，部署后变量缺失 | 部署前确认目标环境变量/配置与 staging 完全对齐 |
| [dep-04-skip-health-check] 跳过健康检查 | 部署完就走，首页都打不开 | 部署后必须跑健康检查：首页/API/console |

## 7-验收 反面模式

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| [uat-01-skip-nonfunctional] 只看功能不看 AC | 漏验收非功能需求（性能/安全/兼容） | 逐条对照 REQUIREMENT.md AC 验证 |
| [uat-02-skip-health-score] 跳过健康评分 | 缺少量化基准，下次无法对比趋势 | 运行 health_scorer.py，评分写入 UAT.md |
| [uat-03-forget-lessons] 忘记 LESSONS | 失败经验不记录，下次重复踩坑 | 扫 SUMMARY/PROGRESS，提名教训入库 |
| [uat-04-progress-not-cleaned] PROGRESS 未清理 | 临时文件残留在 spec 目录 | 验收后删除所有 `*-PROGRESS.md` |
| [uat-05-skip-archive] 跳过归档流程 | 工件散落在 .specs/ 下，难以追溯 | 必须走归档：移动到 archive/ + 更新 STATE + 索引 |

---

## 跨阶段通用反面模式

| Anti-Pattern | Why It Fails | Better Approach |
|---|---|---|
| [cross-01-skip-confirmation] 以"信息充分"跳过交互确认 | Agent 对用户意图的猜测往往偏离实际需求，后续阶段全部返工 | 凡涉及用户决策的环节（需求细节/技术选型/归档原因），必须等待用户显式确认 |
| [cross-02-skip-gate] 以"这个太简单"跳闸门 | 简单变更恰恰是未审查假设导致返工最多的地方 | 见 SKILL.md HARD-GATE：每个 change 都走完整闸门 |
