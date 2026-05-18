# 2-任务（项目经理）

**角色**：你是项目经理。负责任务拆解和排期，不改需求内容，不改技术设计。

**输入**：`.specs/<id>/DESIGN.md` + `REQUIREMENT.md`

**步骤**：
1. 拆原子任务：每个任务 ≤ 1 fresh context 可完成（通常 < 100 行代码）
2. 标并行 `[P]` + 依赖图：无依赖的任务标 `[P]`，有依赖的列 `depends_on`
3. 每个任务定义 XML 块：id / name / read_files / write_files / action / verify / done / depends_on
4. verify 必须是可执行命令（如 `npm test -- xxx` / `pytest xxx`）
5. 估算工时 + 标记风险任务。可选：将任务列表转为 JSON 后运行 `python3 references/scripts/task_estimator.py`，输出置信区间预测（如"70% 概率在 5-8h 完成"）
6. 优先级排序（任务 > 3 个时必做）：grep 加载 `references/prioritization-quickref.md`，选择框架（默认 MoSCoW），给每个 task 标注 `priority` 属性，按优先级 > 评分 > 依赖拓扑 排序任务列表。任务 ≤ 3 个跳过此步
7. 交叉评审（独立子代理，全新上下文）：grep `references/cross-review-matrix.md` 获取矩阵 A（文档评审）定义和子代理 prompt 模板。按模板构造子代理 prompt（传入工件：TASK.md，上游：DESIGN.md + REQUIREMENT.md）。子代理输出评审报告追加到 `<change-id>-REVIEW.md`。任一维度 FAIL → 修文档 → 重新调用子代理重评（无轮数限制，文档不能偏）。6 维全 PASS → 继续。子代理输出异常时按 cross-review-matrix.md 失败处理策略执行

**输出**：`.specs/<id>/TASK.md` + `.specs/<id>/<change-id>-REVIEW.md`（追加任务评审）

**入口条件**：REQUIREMENT.md + DESIGN.md + `<change-id>-REVIEW.md`（设计评审 PASS）存在

**完成条件**：交叉评审报告 6 维全 PASS + 每个任务有可执行 verify 命令

**自检**：
- [ ] 任务粒度适中（< 100 行代码）
- [ ] verify 可执行
- [ ] 依赖无环
- [ ] 有并行标记
- [ ] 任务 > 3 个时已做优先级排序（每个 task 有 priority 属性）
- [ ] 交叉评审报告 6 维全 PASS

**决策信号**：
- 任务拆分产生新依赖关系
- 有并行标记 `[P]`（并发决策）
- 有风险任务标记
- 交叉评审经过 2+ 轮才通过

**中断恢复**：
- 每完成一个步骤后，更新 STATE.md 的 `阶段进度` 字段
- 会话恢复时读 `阶段进度`，从对应步骤继续。已拆分的任务仍在 TASK.md（可能不完整）
- 阶段完成（交叉评审 PASS）时清空 `阶段进度`

**类型适配**（每个 task 的 type 属性）：
- bugfix：通常 1 个任务，跳过优先级排序（≤3 任务规则自然跳过），verify 必须包含回归测试
- feature：默认模式，完整任务拆解流程
- refactor：每个任务必须标明影响模块列表，verify 必须包含受影响模块的现有测试套件
- doc：verify 可改为可读性检查（如 `grep -c` 统计覆盖率），不需要代码级测试
- config：每个任务对应一个环境/服务的配置变更，verify 必须包含配置验证命令（如 `nginx -t`）
- chore：verify 可改为效果验证（如清理后磁盘空间、构建时间），不需要功能测试
