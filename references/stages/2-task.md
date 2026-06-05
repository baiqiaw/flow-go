<!-- output-mode: tight -->
# 2-任务（项目经理）

**角色**：你是项目经理。负责任务拆解和排期，不改需求内容，不改技术设计。

**输入**：`.specs/<id>/DESIGN.md` + `REQUIREMENT.md`

**步骤**：
0. **Worktree 验证**（确认 0-需求阶段已创建 worktree）：
   - (a) 读 `.specs/<id>/STATE.md` 的 `worktree_path` 字段
   - (b) 验证 worktree 目录存在且 `git branch --show-current` 输出 `change/<id>`
   - (c) 验证失败 → 输出「⚠️ worktree 未创建，请确认 SKILL.md 路由层的 worktree 创建流程是否已执行」
1. 拆原子任务：每个任务 ≤ 1 fresh context 可完成（通常 < 100 行代码）
   垂直切片原则：
	   - 每个任务必须是垂直切片：穿透所有相关层（schema→API→UI→测试），完成后可独立验证
	   - 禁止水平切片（按层拆分：如"所有数据库 schema 一个任务、所有 API 一个任务"）
	   - 水平切片信号：任务 action 只涉及单层操作（如"修改数据库表结构"无对应 API 和测试）
	   - 垂直切片验证：任务 done 条件必须包含端到端验证（不只是某一层的通过）
	   - 允许共享 setup/teardown 任务作为独立前序任务（如公共类型定义、数据库 migration）
2. 标并行 `[P]` + 依赖图：无依赖的任务标 `[P]`，有依赖的列 `depends_on`
   AFK/HITL 标记指导：
	   - 每个 task 增加 mode 属性标记（afk / hitl / colab），默认 colab
	   - **AFK**（Away From Keyboard）：可完全交给 AI agent 自动执行
	     * 特征：有明确 action 和 done 条件、无需人工决策、无外部系统依赖
	     * 适合：纯实现任务、有明确测试的任务、文档编写
	   - **HITL**（Human In The Loop）：需要人工决策或操作
	     * 特征：涉及架构决策、设计审阅、外部服务操作、需要人工确认的判断
	     * 适合：设计方案选择、外部 API 调试、需要人工审阅的任务
	   - **COLAB**（Collaborative）：AI + 人协作完成（默认）
	   - 标记原则：优先标记为 AFK（减少人工干预）；不确定时标 COLAB
	   - 并行模式增强：parallel 路由优先将 AFK 任务分配给独立 agent
3. 每个任务定义 XML 块：id / name / read_files / write_files / action / verify / done / depends_on / e2e_coverage / independently_verifiable + 可选的 context_budget / agent_hint
4. verify 必须是可执行命令（如 `npm test -- xxx` / `pytest xxx`）
5. **预检环**（配置项 `preflight_check` 控制，默认开启）：
   - 5a 反幻觉预检：验证每个 task 的 `read_files` glob 模式能匹配到真实文件；验证 `verify` 命令格式包含可执行部分
   - 5b 上下文预算估算（配置项 `context_budget_mode` 控制，默认 auto）：运行 `python3 references/scripts/context_budget_estimator.py --task-file .specs/<id>/TASK.md`，获取每个任务的预算级别（small/medium/large）和分组建议。结果回填到每个 task 的 `<context_budget>` 和 `<agent_hint>` 字段。若配置为 manual，跳过脚本由人工填写；若配置为 off，跳过整步
   - 5c 粒度检查：large 级别任务标记为「建议拆分」，medium 级别记录为「需关注」
   - 5d 更新依赖图描述，增加「并行分组」章节（按分组建议组织：small 并行组 / large 独占组 / 串行链）
6. **迭代精化**（预检不通过时执行，最多 2 轮）：
   - 预检发现问题（路径不存在/粒度过大/上下文溢出）→ 修改 TASK.md（拆分大任务/修正路径/调整 verify）→ 重新执行步骤 5
   - 第 2 轮仍有问题 → 记录到自检清单「预检残留问题」，由后续交叉评审处理
   - 预检全通过 → 直接进入步骤 7
7. 估算工时 + 标记风险任务。可选：将任务列表转为 JSON 后运行 `python3 references/scripts/task_estimator.py`，输出置信区间预测（如"70% 概率在 5-8h 完成"）
8. 优先级排序（任务 > 3 个时必做）：grep 加载 `references/prioritization-quickref.md`，选择框架（默认 MoSCoW），给每个 task 标注 `priority` 属性，按优先级 > 评分 > 依赖拓扑 排序任务列表。任务 ≤ 3 个跳过此步
9. **<HARD-GATE> 交叉评审**（独立子代理，全新上下文）：grep `references/cross-review-matrix.md` 获取矩阵 A（文档评审）定义和子代理 prompt 模板。按模板构造子代理 prompt（传入工件：TASK.md，上游：DESIGN.md + REQUIREMENT.md）。子代理输出评审报告追加到 `<change-id>-REVIEW.md`。任一维度 FAIL → 修文档 → 重新调用子代理重评（无轮数限制，文档不能偏）。6 维全 PASS → 继续。子代理输出异常时按 cross-review-matrix.md 失败处理策略执行。**交叉评审是任务阶段的最后一道质量闸门——未经独立评审的任务拆解，粒度不均、依赖遗漏、verify 不可执行等问题会直接在开发阶段暴露，返工成本远高于评审。此步骤是阶段完成的硬性前置条件，不可跳过。未完成禁止转换到 3-开发。**

**输出**：`.specs/<id>/TASK.md` + `.specs/<id>/<change-id>-REVIEW.md`（追加任务评审）

**入口条件**：REQUIREMENT.md + DESIGN.md + `<change-id>-REVIEW.md`（设计评审 PASS）存在

**完成条件**：交叉评审报告 6 维全 PASS + 每个任务有可执行 verify 命令 + 预检环通过（或残留问题已记录）

**自检**：
- [ ] 任务粒度适中（< 100 行代码）
- [ ] verify 可执行
- [ ] 依赖无环
- [ ] 有并行标记
- [ ] 任务 > 3 个时已做优先级排序（每个 task 有 priority 属性）
- [ ] 预检环已通过（或残留问题已记录在自检清单）
- [ ] context_budget 与估算结果一致（若启用）
- [ ] 并行分组已体现在依赖图描述中（若启用）
- [ ] 交叉评审报告 6 维全 PASS
- [ ] worktree 验证通过（worktree_path 非空且目录存在）
- [ ] 垂直切片检查：每个任务有 e2e_coverage 字段（声明穿透层），done 条件包含端到端验证
- [ ] Tracer bullet 检查：每个任务有 independently_verifiable 字段，优先安排 true 的任务
- [ ] AFK/HITL 标记检查：每个任务有 mode 属性（afk/hitl/colab）

**决策信号**：
- 任务拆分产生新依赖关系
- 有并行标记 `[P]`（并发决策）
- 有风险任务标记
- 交叉评审经过 2+ 轮才通过
- 预检环迭代 2 轮仍有残留问题

**中断恢复**：
- 每完成一个步骤后，更新 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段
- 会话恢复时读 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段，从对应步骤继续。已拆分的任务仍在 TASK.md（可能不完整）
- 阶段完成（交叉评审 PASS）时清空 `阶段进度`

**类型适配**（每个 task 的 type 属性）：
- bugfix：通常 1 个任务，跳过优先级排序（≤3 任务规则自然跳过），verify 必须包含回归测试
- feature：默认模式，完整任务拆解流程
- refactor：每个任务必须标明影响模块列表，verify 必须包含受影响模块的现有测试套件
- doc：verify 可改为可读性检查（如 `grep -c` 统计覆盖率），不需要代码级测试
- config：每个任务对应一个环境/服务的配置变更，verify 必须包含配置验证命令（如 `nginx -t`）
- chore：verify 可改为效果验证（如清理后磁盘空间、构建时间），不需要功能测试

**配置项**：
- `preflight_check`（默认 true）：开启预检环（步骤 5-6）。关闭后恢复原有线性 7 步流程
- `context_budget_mode`（默认 auto）：auto=脚本自动估算 / manual=手动填写 / off=不使用上下文预算

## 上下文需求清单

| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |
| DESIGN.md | 架构图 | 必选 | 原文保留 |
| DESIGN.md | API 设计 | 必选 | 原文保留 |
| DESIGN.md | ADR | 必选 | 标题+决策行 |
| DESIGN.md | 风险 | 可选 | 标题+缓解行 |
| DESIGN.md | 既有架构对齐 | 必选 | 原文保留 |
