# 特殊流程

> 热修 / 归档 / 废弃 / 回溯 / 归档维护。SKILL.md 路由后按流程名 grep 加载。

---

## 热修

**角色**：开发员（修）→ 技术经理（审），跳过需求和设计阶段

**输入**：STATE.md + bug 描述/用户报告 + 最近 SUMMARY.md（如存在）

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

**输入**：STATE.md + `.specs/<id>/` 下所有已有工件

**触发**：
- 用户说"归档/archive/收工/这个做完了"
- 用户明确表示当前 spec 不需要继续后续阶段

**步骤**：
1. 确认归档目标：取 STATE.md 的 `活跃 Change`（必须非空）
2. 阶段盘点：检查 `.specs/<id>/` 下已有的工件文件，列出已完成阶段
3. 归档原因确认：询问用户归档原因（正常完成/不需要后续阶段/需求变更/其他）
4. 写归档记录：在 spec 目录下创建归档文件
   - 已到 7-验收且 UAT 通过 → UAT.md 已有归档段，无需额外文件
   - 未到 7-验收 → 创建 ARCHIVE.md（见 `artifacts/spec-artifacts.md`）
4.5. 轨迹采集：执行 `python3 references/scripts/trace_collector.py --specs-dir .specs/<id> --change-id <id>`，生成 `.specs/<id>/TRACE.md` 和追加 `.specs/traces.jsonl`。采集失败不阻塞归档（输出警告继续执行）
5. LESSONS 提名：扫已有 SUMMARY 和 PROGRESS，符合提名条件的入库
6. 临时文件清理：删除 spec 目录下所有 `*-PROGRESS.md`
   > ⚠️ 步骤 7-9 必须严格按顺序执行，不允许跳步。STATE.md 清空（步骤 9）必须在目录移动（步骤 7）和索引更新（步骤 8）完成后才执行。
7. 移动归档：执行 `mv .specs/<id>/ .specs/archive/<date>-<id>/`（date 格式 YYYYMMDD；如 archive 目录不存在则先 `mkdir -p .specs/archive`）。**必须在步骤 8 之前完成**，因为索引指向移动后的路径
8. 更新归档索引：读 `.specs/archive/ARCHIVE-INDEX.md`（不存在则按 `meta-artifacts.md` 模板创建），追加新归档条目到清单表格，更新归档统计
9. STATE.md 清理：活跃 Change / 当前阶段 / 当前任务 / 中断任务 全部清空

**输出**：`.specs/archive/<date>-<id>/` + STATE 更新

**闸门**：用户确认归档（必须显式确认原因）

**自检**：
- [ ] 归档目标已确认（非空、非 archive）
- [ ] 已有工件已盘点
- [ ] 归档原因已记录
- [ ] 轨迹已采集（TRACE.md 已生成，traces.jsonl 已追加；采集失败不影响归档）
- [ ] PROGRESS.md 已清理
- [ ] spec 目录已移动到 `.specs/archive/<date>-<id>/`（原路径已不存在）
- [ ] 归档索引已更新
- [ ] STATE.md 已清空

**决策信号**：不适用（归档不产生决策，只记录状态）

> 归档完成后，主流程第七步的决策同步检查将加载 `references/sync-workflow.md` 执行 **受作用域同步**（仅同步本次归档涉及的文档）。

---

## 废弃

**角色**：项目经理。评估废弃影响并执行，不改代码。

**输入**：STATE.md + 用户指定要废弃的 change-id（或当前活跃 Change）

**触发**：
- 用户说"废弃/放弃/abandon/cancel"
- 回溯流程检测搁置超 60 天时建议

**步骤**：
1. 确认废弃目标：
   - 用户指定了 change-id → 确认 `.specs/<id>/` 存在
   - 用户未指定 → 取 STATE.md 的 `活跃 Change`
   - 都没有 → 列出 `.specs/` 下所有非 archive 目录，让用户选
2. 废弃影响评估：列出已到达阶段 + 代码提交状态 + 并行依赖
3. 写 ABANDONED.md（见 `artifacts/deploy-artifacts.md`）
4. 临时文件清理：删除所有 `*-PROGRESS.md`
5. 移动归档：`.specs/<id>/` → `.specs/archive/abandoned/<date>-<id>/`
6. 更新归档索引
7. STATE.md 清理（如废弃的是活跃 Change → 清空全部字段）
8. LESSONS 提名（从 PROGRESS 中提取已排除方案）
9. outcome 标记：如 `.specs/traces.jsonl` 存在该 change-id 的记录且 `outcome` 为 null，更新为 `abandoned`（无需运行 trace_collector，直接原地修改 traces.jsonl 对应行）

**输出**：`.specs/archive/abandoned/<date>-<id>/ABANDONED.md` + STATE 更新

**闸门**：用户显式确认废弃

**自检**：
- [ ] 废弃目标已确认
- [ ] 影响评估已输出（阶段进度 + 代码状态 + 依赖检查）
- [ ] ABANDONED.md 已写入
- [ ] PROGRESS.md 已清理
- [ ] 归档索引已更新
- [ ] STATE.md 已更新（如适用）

**决策信号**：不适用（废弃不产生决策，只记录理由）

---

## 回溯

**角色**：自动，无特定角色。负责恢复上下文，不做业务决策。

**输入**：STATE.md（必须存在）

**步骤**：
1. 读 STATE.md（活跃 Change / 当前阶段 / 中断任务）
2. 读最近 3 个 `<task-id>-SUMMARY.md`
3. 读 `.specs/LESSONS.md`
4. grep 待办（`TODO` / `FIXME` / `HACK`）
5. 搜索历史类似问题：grep `.lessons.jsonl`（如存在）中的关键词
6. 输出"5 分钟项目摘要 + 推荐下一步"
7. 健康趋势（如 `.specs/health-trends.jsonl` 存在）：展示最近 5 个 Change 的评分趋势，标注退步领域和改进领域
8. 如搁置超 30 天（对比 STATE.md 更新时间），额外做 bit rot 检查（依赖更新/CI 状态/测试是否还能通过）
9. 归档扫描：`ls .specs/archive/` 和 `ls .specs/archive/abandoned/`（如存在），输出归档统计（总数 / 最旧 / 最新）
10. 归档老化提醒：如存在归档超过 90 天的目录，在恢复建议中追加"归档清理建议"；如活跃 Change 搁置超 60 天，建议考虑废弃

**输出**：项目摘要 + 阶段恢复建议

**闸门**：用户确认恢复目标阶段

**自检**：
- [ ] STATE.md 已读
- [ ] 最近 3 个 SUMMARY 已扫
- [ ] 搁置时长已检查
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
