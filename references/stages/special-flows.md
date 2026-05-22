# 特殊流程

> 热修 / 归档 / 废弃 / 回溯 / 归档维护。SKILL.md 路由后按流程名 grep 加载。

---

## 热修

**角色**：开发员（修）→ 技术经理（审），跳过需求和设计阶段

**输入**：STATE.md（索引表）+ `.specs/<id>/STATE.md`（change 级详情）+ bug 描述/用户报告 + 最近 SUMMARY.md（如存在）

**分级**：
- P0（完全不可用）：先回滚再诊断，不许没回滚就查代码
- P1（部分功能炸）：3 问澄清后直接修
- P2（边缘问题）：建议走正常流程

**步骤**：
1. 判定 P 等级
2. P0 先回滚，P1/P2 按级别处理
3. **根因分析**（Iron Law — 无根因不修复）：
   - 收集症状：错误信息、复现条件、最近变更
   - 检查 LESSONS.md 和 `.lessons.jsonl` 历史类似问题
   - 形成根因假设（最多 3 个）
   - 逐个验证假设，3 个都失败 → 停下升级给用户
   - **作用域锁定**：确定相关目录后限制编辑范围，防止"顺手改了别的"
4. 修复 → 测试 → 审查（精简版）
5. **Blast radius check**：修复涉及 > 5 文件时必须确认
6. 事后 24h 内补齐：CHANGE.md + TEST.md + LESSONS 提名
7. **进化反思（热修自动触发）**：运行 `evolution_signal.py`（热修 = 最强的 struggle_success 信号）+ `evolution_reflect.py`，假设直接提交 LESSONS 提名（无需 2 次门槛）

**输出**：修复代码 + CHANGE.md + TEST.md

**闸门**：修复验证通过 + 事后补齐完成

**红线**：热修不能成为"绕过流程的捷径"。事后补齐是强制的。

**自检**：
- [ ] P 等级已判定
- [ ] 根因已分析（非直接跳到修复）
- [ ] 作用域已锁定（编辑范围限于相关目录）
- [ ] 事后补齐完成（CHANGE.md + TEST.md + LESSONS）
- [ ] 进化反思已运行（信号检测 + 假设 → LESSONS）
- [ ] 未绕过正常流程（有正当理由）

**决策信号**：
- P 等级判定为 P0 或 P1
- 事后补齐产生了新的 LESSONS 提名

---

## 归档

**角色**：当前阶段对应角色。负责将 spec 从任意阶段安全归档。

**输入**：STATE.md（索引表）+ `.specs/<id>/STATE.md`（change 级详情）+ `.specs/<id>/` 下所有已有工件

**触发**：
- 用户说"归档/archive/收工/这个做完了"
- 用户明确表示当前 spec 不需要继续后续阶段

**步骤**：
1. 确认归档目标：取 STATE.md 索引表的 `活跃 Change`（必须非空）
2. 阶段盘点：检查 `.specs/<id>/` 下已有的工件文件，列出已完成阶段
3. 归档原因确认：询问用户归档原因（正常完成/不需要后续阶段/需求变更/其他）
3.5. **Worktree 合并与清理**（如 per-change STATE.md 的 `worktree_path` 非空）：
   - (a) ExitWorktree 退出 worktree，回到主仓库
   - (b) `git checkout main` 确保在 main 分支
   - (c) `git merge change/<id>` 将分支合并到 main
   - (d) STATE.md 冲突：接受 main 版本（`git checkout --ours STATE.md`），然后执行本流程步骤 9 的 STATE.md 清理
   - (e) 其他冲突：停下来提示用户手动解决
   - (f) `git worktree remove <worktree_path>` 删除 worktree
   - (g) `git branch -d change/<id>` 删除分支
   - (h) per-change STATE.md 的 `worktree_path` 清为 `无`
   - worktree_path 为空 → 跳过本步骤
   - 详细流程见 `references/worktree-lifecycle.md`「归档合并流程」章节
4. 写归档记录：在 spec 目录下创建归档文件
   - 已到 7-验收且 UAT 通过 → UAT.md 已有归档段，无需额外文件
   - 未到 7-验收 → 创建 ARCHIVE.md（见 `artifacts/spec-artifacts.md`）
4.5. 轨迹采集：执行 `python3 references/scripts/trace_collector.py --specs-dir .specs/<id> --change-id <id>`，生成 `.specs/<id>/TRACE.md` 和追加 `.specs/traces.jsonl`。采集失败不阻塞归档（输出警告继续执行）
4.6. **进化信号自动写入 LESSONS**（AC-6）：执行 `python3 references/scripts/evolution_signal.py --specs-dir .specs/<id> --write-lessons`，将 strong_signals 格式化写入 `.specs/LESSONS.md` 的"待改进领域"章节。无 strong_signals 时输出提示并跳过
4.6b. **热修反馈分析**（可选）：如 `.specs/<id>/user-inputs.jsonl` 存在且行数 > 5 → 运行 `python3 references/scripts/feedback_classifier.py --specs-dir .specs/<id> --complexity LITE`。有 skill 反馈 → 追加到 `.specs/evolution/skill-feedback.jsonl`，输出「🔥 热修反馈已捕获：skill N 条」。行数 ≤ 5 时跳过
5. LESSONS 提名：扫已有 SUMMARY 和 PROGRESS，符合提名条件的入库
6. 临时文件清理：删除 spec 目录下所有 `*-PROGRESS.md`
   > ⚠️ 步骤 7-9 必须严格按顺序执行，不允许跳步。STATE.md 清理（步骤 9：索引表移除 + `.specs/<id>/STATE.md` 删除）必须在目录移动（步骤 7）和索引更新（步骤 8）完成后才执行。
7. 移动归档：执行 `mv .specs/<id>/ .specs/archive/<date>-<id>/`（date 格式 YYYYMMDD；如 archive 目录不存在则先 `mkdir -p .specs/archive`）。**必须在步骤 8 之前完成**，因为索引指向移动后的路径
8. 更新归档索引：读 `.specs/archive/ARCHIVE-INDEX.md`（不存在则按 `meta-artifacts.md` 模板创建），追加新归档条目到清单表格，更新归档统计
8.1. **PIPELINE.md 状态更新**（如 PIPELINE.md 存在）：将当前归档 change 的状态从 `active` 改为 `completed`
8.5. **Pipeline 衔接检查**：读取 `.specs/PIPELINE.md`（如存在），找下一个 `pending` change（按优先级排序，依赖已完成）。找到 → 项目级 STATE.md 写入 `Pipeline 待续` 字段 → 输出「📋 Pipeline 下一个：{change-id} — {描述}」→ 询问用户是否立即开始。用户确认 → 走 AC-4 启动流程（清空 Pipeline 待续 → PIPELINE.md 标记 active → 创建目录 → STATE.md 索引表新增该 change 行 → 创建 `.specs/<id>/STATE.md` 初始状态 → 路由到 0-需求）。用户拒绝 → 保留 Pipeline 待续 字段。PIPELINE.md 不存在或无 pending → 跳过
9. STATE.md 清理：从 STATE.md 索引表移除该 change 行 + 删除 `.specs/<id>/STATE.md`。**注意**：`Pipeline 待续` 字段如步骤 8.5 已写入，则保留不清空
9.5. **成功指标**（归档完成时输出，供用户快速判断 flow-go 是否生效）：
    - Diff 中无关改动行数是否减少？（对比上次归档 diff）
    - 因假设错误导致的返工是否减少？（回顾本 change 是否有因猜测导致的返工）
    - 澄清问题是否在实现前提出？（回顾需求/设计阶段的提问记录）
    > 三项全 ✅ → flow-go 流程在生效。有 ❌ → 下个 change 重点关注该环节。
9.6. **受作用域同步**：加载 `references/sync-workflow.md` 执行受作用域同步（仅同步本次归档涉及的文档）。扫描归档工件中的决策记录，将涉及的架构/API/数据库变更同步到 CLAUDE.md / CONTEXT.md / docs/ 对应章节。同步完成后输出摘要：`🔄 同步完成：CLAUDE.md 更新 X 处，CONTEXT.md 更新 Y 处`。如本次归档无决策性变更 → 输出「同步跳过：本次归档无决策性变更」并继续。**如已在 7-验收 步骤 8 执行过全量同步，跳过本步骤**（全量同步已覆盖受作用域同步的范围）
10. **Git 归档提交**：将所有归档相关变更纳入一次提交
    - (a) `git add STATE.md .specs/archive/ .specs/ARCHIVE-INDEX.md`（归档索引和主状态）
    - (b) `git add .specs/traces.jsonl .specs/health-history.jsonl`（如存在，轨迹和健康记录）
    - (c) `git add .specs/LESSONS.md .specs/evolution/ .specs/PIPELINE.md`（如存在，进化产物和 Pipeline）
    - (d) `git add .specs/CONTEXT.md .specs/adr/`（如本次归档有更新）
    - (e) `git status` 检查是否还有未纳入的 `.specs/` 或项目根目录相关文件 → 有则补充 add
    - (f) `git commit`，消息格式：`archive(<change-id>): 归档完成，N/N AC全PASS，健康评分XX/X级`
    - **禁止**使用 `git add .` 或 `git add -A`，必须逐项 add 避免纳入无关文件
11. **Git push + clean 验证**：
    - (a) `git push`
    - (b) `git status` — 必须满足以下全部条件才算归档完成：
      - `working tree clean`（无 staged、unstaged、untracked 文件）
      - `up to date with 'origin/main'`（不 ahead/behind）
    - (c) 不满足 → 排查遗漏文件，补充 add + commit + push，回到 (b)

**输出**：`.specs/archive/<date>-<id>/` + STATE.md 索引表更新 + `.specs/<id>/STATE.md` 已删除 + git 已 push + working tree clean + 知识库同步完成

**闸门**：用户确认归档（必须显式确认原因）

**自检**：
- [ ] 归档目标已确认（非空、非 archive）
- [ ] 已有工件已盘点
- [ ] 归档原因已记录
- [ ] 轨迹已采集（TRACE.md 已生成，traces.jsonl 已追加；采集失败不影响归档）
- [ ] PROGRESS.md 已清理
- [ ] spec 目录已移动到 `.specs/archive/<date>-<id>/`（原路径已不存在）
- [ ] 归档索引已更新
- [ ] Pipeline 衔接已检查（PIPELINE.md 存在时）
- [ ] STATE.md 已清理（索引表移除该 change 行 + `.specs/<id>/STATE.md` 已删除；Pipeline 待续 保留如有写入）
- [ ] worktree 已合并并清理（如适用）
- [ ] 归档变更已 git commit（STATE.md + archive/ + traces + health + evolution 等）
- [ ] 已 git push 且 `git status` 显示 `working tree clean` + `up to date with 'origin/main'`
- [ ] 受作用域同步已执行（加载 sync-workflow.md，输出同步摘要或跳过原因）

**决策信号**：归档完成触发受作用域同步（步骤 9.6 已内联执行，不依赖 SKILL.md 第七步信号检查）

---

## 中断

**角色**：当前阶段对应角色。负责将未完成 change 安全暂停。

**输入**：STATE.md（索引表）+ `.specs/<id>/STATE.md`（change 级详情）+ `.specs/<id>/` 下所有已有工件 + `.specs/PIPELINE.md`（如存在）

**触发**：
- 用户请求暂停/切换 change
- 用户需要处理更紧急的事
- 当前 change 未走完全流程需要搁置

**步骤**：
1. 确认中断目标：取 STATE.md 索引表的 `活跃 Change`（必须非空）
2. 中断确认：询问用户确认中断（区别于归档）— 输出「⚠️ 中断 {change-id}，当前阶段 {stage}，工件保留在 .specs/<id>/，可随时恢复。确认中断？」
3. PIPELINE.md 更新（如存在）：将该 change 的状态从 `active` 改为 `interrupted`
4. STATE.md 更新：`.specs/<id>/STATE.md` 的 `中断任务` 字段写入当前阶段信息（如 `3-开发/T02`），`当前阶段` 和 `当前任务` 清空；STATE.md 索引表移除该 change 行
   - `worktree_path` 保持不变（worktree 保留，供恢复时重入）
5. 输出恢复提示：「📋 {change-id} 已中断。恢复方式：输入 `继续` 或 `resume`」
   - 如 `worktree_path` 非空 → 追加提示「worktree 保留在 <path>，恢复时将自动进入」

**输出**：STATE.md 索引表更新 + `.specs/<id>/STATE.md` 更新 + PIPELINE.md 状态更新

**闸门**：用户显式确认中断（必须区分于归档）

**自检**：
- [ ] 中断目标已确认（活跃 Change 非空）
- [ ] 中断已确认（非归档）
- [ ] PIPELINE.md 状态已更新（如存在）
- [ ] STATE.md 已更新（`.specs/<id>/STATE.md` 中断任务有值、当前阶段和当前任务已清空；索引表已移除该 change 行）
- [ ] 恢复提示已输出

**决策信号**：不适用（中断不产生决策，只记录状态）

---

## 并行启动

**角色**：自动。负责并行启动新 change 并检测冲突。

**输入**：STATE.md（索引表）+ `.specs/PIPELINE.md` + 用户指定的新 change-id

**触发**：
- 用户请求并行启动新 change（当前已有 active change）
- 用户说"并行" / "parallel" / "同时开始"

**步骤**：
1. 确认并行目标：用户指定或从 PIPELINE.md pending 列表选择
2. **文件范围冲突检测**：读取 PIPELINE.md 中所有 `active` change 的 `文件范围` 列，与新 change 的文件范围做 glob 重叠检测
3. 无冲突 → 继续；有冲突 → 输出「⚠️ 冲突：{新change} 的文件范围与 active {已有change} 重叠（{重叠路径}）」，建议串行执行或调整范围，阻止并行启动
4. PIPELINE.md 更新：新 change 状态改为 `active`
5. STATE.md 更新：索引表新增新 change 行 + 创建 `.specs/<id>/STATE.md`（初始阶段：0-需求，当前任务：无）
6. 路由到新 change 的 0-需求阶段（复用拆分时的需求信息）

**输出**：PIPELINE.md 更新 + STATE.md 索引表更新 + `.specs/<id>/STATE.md` 已创建

**闸门**：用户确认并行启动 + 文件范围无冲突

**自检**：
- [ ] 并行目标已确认
- [ ] 文件范围冲突检测已执行
- [ ] 无冲突时 PIPELINE.md 已更新
- [ ] STATE.md 索引表已新增 change 行 + `.specs/<id>/STATE.md` 已创建
- [ ] 冲突时已阻止并提示

**决策信号**：不适用

**角色**：项目经理。评估废弃影响并执行，不改代码。

**输入**：STATE.md（索引表）+ `.specs/<id>/STATE.md`（change 级详情）+ 用户指定要废弃的 change-id（或当前活跃 Change）

**触发**：
- 用户说"废弃/放弃/abandon/cancel"
- 回溯流程检测搁置超 60 天时建议

**步骤**：
1. 确认废弃目标：
   - 用户指定了 change-id → 确认 `.specs/<id>/` 存在
   - 用户未指定 → 取 STATE.md 索引表的 `活跃 Change`
   - 都没有 → 列出 `.specs/` 下所有非 archive 目录，让用户选
2. 废弃影响评估：列出已到达阶段 + 代码提交状态 + 并行依赖
3. 写 ABANDONED.md（见 `artifacts/deploy-artifacts.md`）
4. 临时文件清理：删除所有 `*-PROGRESS.md`。user-inputs.jsonl 不删除，随目录移动到归档
4.5. **Worktree 清理**（如 per-change STATE.md 的 `worktree_path` 非空）：
   - (a) ExitWorktree 退出 worktree
   - (b) `git worktree remove --force <worktree_path>` 强制删除（丢弃改动）
   - (c) `git branch -D change/<id>` 强制删除分支（不合并）
   - worktree_path 为空 → 跳过本步骤
   - 详细流程见 `references/worktree-lifecycle.md`「废弃清理流程」章节
5. 移动归档：`.specs/<id>/` → `.specs/archive/abandoned/<date>-<id>/`（含 user-inputs.jsonl）
6. 更新归档索引
7. STATE.md 清理（如废弃的是活跃 Change → 从索引表移除该 change 行 + 删除 `.specs/<id>/STATE.md`）
8. LESSONS 提名（从 PROGRESS 中提取已排除方案）
9. outcome 标记：如 `.specs/traces.jsonl` 存在该 change-id 的记录且 `outcome` 为 null，更新为 `abandoned`（无需运行 trace_collector，直接原地修改 traces.jsonl 对应行）

**输出**：`.specs/archive/abandoned/<date>-<id>/ABANDONED.md` + STATE.md 索引表更新 + `.specs/<id>/STATE.md` 已删除

**闸门**：用户显式确认废弃

**自检**：
- [ ] 废弃目标已确认
- [ ] 影响评估已输出（阶段进度 + 代码状态 + 依赖检查）
- [ ] ABANDONED.md 已写入
- [ ] PROGRESS.md 已清理
- [ ] 归档索引已更新
- [ ] STATE.md 已更新（索引表已移除该 change 行 + `.specs/<id>/STATE.md` 已删除，如适用）
- [ ] worktree 已清理（如适用）

**决策信号**：不适用（废弃不产生决策，只记录理由）

---

## 回溯

**角色**：自动，无特定角色。负责恢复上下文，不做业务决策。

**输入**：STATE.md（索引表，必须存在）+ `.specs/<id>/STATE.md`（change 级详情，如存在）

**步骤**：
1. 读 STATE.md 索引表（活跃 Change / Pipeline 待续），如有活跃 Change 则读取对应 `.specs/<id>/STATE.md`（当前阶段 / 当前任务 / 中断任务 / 阶段进度）
1.5. **Worktree 重入**（如目标 change 的 `worktree_path` 非空）：
   - worktree_path 非空且 `test -d <path>` → EnterWorktree（path: <path>）进入
   - 非空但目录不存在 → 输出「⚠️ worktree 已丢失：<path>，建议手动恢复或废弃」
   - worktree_path 为空 → 留在主仓库
2. **Pipeline 待续检查**：`Pipeline 待续` 非空且 `活跃 Change` 为空 → 优先输出「📋 Pipeline 待续：{change-id}，要开始吗？」，用户确认后走 AC-4 启动流程
3. 读最近 3 个 `<task-id>-SUMMARY.md`
4. 读 `.specs/LESSONS.md`
5. grep 待办（`TODO` / `FIXME` / `HACK`）
6. 搜索历史类似问题：grep `.lessons.jsonl`（如存在）中的关键词
7. 输出"5 分钟项目摘要 + 推荐下一步"
8. 健康趋势（如 `.specs/health-trends.jsonl` 存在）：展示最近 5 个 Change 的评分趋势，标注退步领域和改进领域
9. 如搁置超 30 天（对比 STATE.md 更新时间），额外做 bit rot 检查（依赖更新/CI 状态/测试是否还能通过）
10. 归档扫描：`ls .specs/archive/` 和 `ls .specs/archive/abandoned/`（如存在），输出归档统计（总数 / 最旧 / 最新）
11. **未归档 change 扫描**：扫描 `.specs/` 下所有非 `archive/`、`evolution/` 的子目录，列出未归档 change。如有 PIPELINE.md 则从 pipeline 读取状态（interrupted 的 change 列为可恢复候选）
12. **残留锁检测**：扫描 `.specs/` 下所有 `.lock` 文件，检查对应任务是否已有 SUMMARY.md（有 SUMMARY 的锁视为残留，提示清理）
13. 归档老化提醒：如存在归档超过 90 天的目录，在恢复建议中追加"归档清理建议"；如活跃 Change 搁置超 60 天，建议考虑废弃

**输出**：项目摘要 + 阶段恢复建议

**闸门**：用户确认恢复目标阶段

**自检**：
- [ ] STATE.md 已读（索引表 + `.specs/<id>/STATE.md` 如存在）
- [ ] Pipeline 待续已检查
- [ ] 最近 3 个 SUMMARY 已扫
- [ ] 搁置时长已检查
- [ ] 未归档 change 已扫描
- [ ] 残留锁已检测
- [ ] 归档统计已输出

**决策信号**：不适用（回溯不产生决策，只恢复上下文）

---

## 归档维护

**角色**：运维。负责归档目录的维护。

**输入**：`.specs/archive/ARCHIVE-INDEX.md`（不存在则扫描目录生成）

**触发**：
- 用户说"清理归档/归档维护"
- 回溯流程检测到超 90 天归档时建议

**步骤**：
1. 读 ARCHIVE-INDEX.md（不存在则扫描 `.specs/archive/` 生成）
2. 列出所有超 90 天的归档目录，标记为"可清理"
3. 展示清单，逐条让用户确认（保留 / 删除）
4. 执行删除：用户确认的目录执行清理
5. 更新 ARCHIVE-INDEX.md
6. 输出摘要：删除了 N 个，保留了 M 个

**输出**：更新后的 ARCHIVE-INDEX.md + 清理摘要

**闸门**：用户逐条确认删除清单

**自检**：
- [ ] ARCHIVE-INDEX.md 已更新
- [ ] 删除的目录确实是用户确认的
- [ ] 未删除 90 天内的归档（除非用户显式要求）

**决策信号**：不适用
