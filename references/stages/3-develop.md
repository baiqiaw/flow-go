<!-- output-mode: caveman -->



# 3-开发（开发员）







**角色**：你是开发员。只执行 TASK.md 中的一个任务。不改 REQUIREMENT/DESIGN。







**输入**：TASK.md 当前任务 + DESIGN.md `## 0` 段 + CONTEXT.md + LESSONS.md







**步骤**：



0. **Worktree 上下文验证**（HARD-GATE — 未通过禁止继续任何文件操作）：



   - (a) 执行 `git branch --show-current`，确认输出为 `change/<id>`。**不是 `change/<id>` → 文件会写入主仓库，破坏隔离性**



   - (b) 执行 `pwd`，确认路径包含 `.claude/worktrees/` 或与 STATE.md 的 `worktree_path` 一致



   - (c) (a) 或 (b) 不满足 → 立即调用 `EnterWorktree(path: <worktree_path>)` 重新进入



   - (d) 重新进入后再次验证 (a)(b)。仍失败 → **停止所有文件操作**，输出「❌ worktree 上下文丢失，当前在 {pwd}，预期在 {worktree_path}。所有代码变更和工件必须在 worktree 中完成」



   - **为什么这很重要**：开发阶段的所有文件变更（代码文件、测试文件、SUMMARY、PROGRESS、.lock）必须全部在 worktree 中完成。写入主仓库会导致：(1) 代码改动脱离 `change/<id>` 分支管理 (2) 归档时 git merge 遗漏文件 (3) 后续返工修复路径问题。这是开发阶段最基本的安全保障——文件写错位置，后续所有流程都是白费



1. 读任务定义，有歧义就停下来反问。参考 `e2e_coverage` 确保实现穿透声明的所有层，`independently_verifiable=true` 的任务必须可独立验证



2. **LESSONS 前置提醒**（AC-7）：grep `.specs/LESSONS.md` 中与当前 change 类型匹配的"待改进领域"条目，输出前置提醒。无匹配则跳过



3. **策略复用**（可选）：grep `.specs/evolution/strategies.jsonl` 中 task_type 匹配的条目，取 score 最高的 1-2 条作为参考，声明「参考成功策略：{approach}（评分 {score}）」。无匹配则跳过



3. **前置健康检查**：运行项目 linter/typecheck/test，确认基线状态。**任何失败必须先修复再继续开发**——不区分"是否本次变更导致"，全部视为阻塞项



4. grep 沿用既有抽象：HTTP 请求 / 日期格式化 / 状态管理等，找到就用



5. 扫 LESSONS.md + `.lessons.jsonl`（如存在）：用任务关键词 grep，命中的条目声明"差异是 X"



6. **锁检查**：读取 `.specs/<id>/.lock`（如存在），检查 `task_id` 是否为当前任务 — 非当前任务则阻止并输出「🔒 任务 {id} 正在由 {agent_id} 执行」；锁检查通过后写入 `.specs/<id>/.lock`（JSON：task_id + files 列表 + agent_id + timestamp）。.lock 不存在则直接创建



7. TDD：RED（先写失败测试）→ GREEN（最少代码通过）→ REFACTOR（测试保护下整理）



8. **结构化调试子流程**（开发员遇到 bug 时进入）：







   **快速路径**：如果 bug 可一步复现且修复简单，可跳过 Phase 3-4，直接修复。







   **Phase 1 — 建反馈闭环**（核心阶段，投入最多时间）：



   这是整个调试流程的关键。拥有快速、确定性、可自动运行的 pass/fail 信号 = 解决 90% 的 bug。



   构建反馈闭环的 10 种方式（按优先级排列）：



   1. 失败测试（unit/integration/e2e，优先选择能触达 bug 的最薄 seam）



   2. curl / HTTP 脚本（对运行中的 dev server）



   3. CLI 调用 + fixture 输入（diff stdout 与已知正确快照）



   4. 无头浏览器脚本（Playwright / Puppeteer）



   5. 回放捕获的 trace（网络请求/事件日志）



   6. 抛弃型 harness（最小子系统 + mock deps）



   7. 属性/模糊测试（1000 随机输入找失败模式）



   8. bisect harness（git bisect run 自动化）



   9. 差分循环（同输入跑旧版 vs 新版，diff 输出）



   10. HITL bash 脚本（人工点击，脚本驱动流程）







   迭代优化循环本身：



   - 能更快吗？（缓存 setup、跳过无关 init、缩小测试范围）



   - 能更尖锐吗？（断言具体症状而非"没崩溃"）



   - 能更确定吗？（固定时间、种子 RNG、隔离文件系统）



   - 2 秒确定性循环 > 30 秒不稳定循环







   非确定性 bug：目标是提高复现率。50% 复现率可调试，1% 不可调试。循环触发 100 次、并行化、加压、缩小时间窗口。



   确实无法建循环 → 停下说明原因，不继续猜测。







   **Phase 2 — 复现**：



   - 运行 Phase 1 的循环，确认 bug 出现



   - 确认复现的是用户描述的 bug（不是附近的其他 bug）



   - 确认可跨多次运行稳定复现



   - 捕获确切症状（错误消息、错误输出、慢时序）







   **Phase 3 — 可证伪假设**：



   - 生成 3-5 个排好序的假设



   - 每个假设必须可证伪："如果 X 是原因，那么改 Y 会让 bug 消失 / 改 Z 会让它变严重"



   - 说不出预测的假设是直觉，不是假设 → 丢弃或锐化



   - 展示给用户后再验证（用户有领域知识可快速重排）



   - 用户不在时按自己的排序继续







   **Phase 4 — 探测**：



   - 每个探测映射到 Phase 3 的具体假设



   - 一次只改一个变量



   - 偏好：调试器/REPL 断点 > 靶向日志 > "全量 log+grep"



   - 所有调试日志用固定前缀标记：`[DEBUG-a4f2]`（后续 grep 一次清理）







   **Phase 5 — 修复 + 回归测试**：



   - 先写回归测试再修复（回归测试在修复前必须是失败的）



   - 如果没有合适的测试 seam → 记录为架构问题（代码结构阻止了 bug 被锁定）



   - 回归测试通过后，重新运行 Phase 1 的完整反馈循环







   **Phase 6 — 清理 + 事后分析**：



   - 确认：原复现步骤不再复现



   - 确认：回归测试通过



   - 清理：grep `[DEBUG-...]` 删除所有临时日志



   - 清理：删除抛弃型原型/harness



   - 提交消息包含正确的假设："原因是 X，通过 Y 修复"



   - 事后分析："什么能防止这个 bug 再次出现？"→ 如涉及架构变更，建议后续重构



9. 跑 verify：贴出真实命令输出。**verify 必须全部通过（0 失败）**——不区分失败来源，任何测试失败都是阻塞项，禁止以"不是本次变更导致"为由绕过。未通过不标记完成



9a. **Guard 回归防护**（guard_enabled=true 时执行）：



    - 读取当前 task 的 `<guard>` 字段（如无则跳过本步骤）



    - 运行 guard 命令，超时阈值：`guard_timeout`（默认 30 秒）



    - 通过（exit 0）→ 继续下一步



    - 失败（exit non-0）→ `git checkout -- <write_files>` 回滚该 task 改动，记录到 SUMMARY.md「Guard 失败」章节，停止当前 task



    - 超时 → 告警「⚠️ Guard 超时（{N}s），不阻塞」，继续下一步



    - **约束**：guard 命令不可修改 write_files 中的文件；guard 文件不在 write_files 范围内



9. **提交前 worktree 路径校验**（HARD-GATE）：



    - 再次执行 `git branch --show-current`，确认仍为 `change/<id>`（防止步骤 7-8 期间 CWD 被意外切换）



    - 执行 `git diff --name-only`，逐条检查每个变更文件路径是否在 worktree 内（而非主仓库）



    - 发现变更在主仓库 → `git checkout -- <主仓库路径>` 回退主仓库改动，重新在 worktree 中执行对应修改



    - **为什么需要二次检查**：步骤 7-8（verify/调试）可能触发子进程或工具调用，某些操作会隐式将 CWD 切回主仓库。此检查是最后的安全网



10. 提交前 diff 边界检查：`git diff --name-only` vs TASK 的 write_files，越界则停下



11. 写 SUMMARY（含交叉评审章节）——**确认 `pwd` 仍在 worktree 内再写**



12. **锁释放**：确认 SUMMARY.md 已写入后删除 `.specs/<id>/.lock`



13. 交叉评审（独立子代理，全新上下文）：



    grep `references/cross-review-matrix.md` 获取矩阵 B（代码评审）定义和子代理 prompt 模板。按模板构造子代理 prompt（传入工件：git diff + TASK + DESIGN + SUMMARY，上游：DESIGN.md）。



    ```



    loop {



      调用独立子代理 → 矩阵 B 6 维检查



      任一维度 FAIL → 修代码（**在 worktree 中修改，修前验证 CWD**） → 重跑 verify → 回到 loop 开头重新调用子代理



      6 维全 PASS → 退出 loop



      超过 3 轮仍有 FAIL → 停下报告用户



    }



    ```



    子代理评审结果写入 SUMMARY.md 交叉评审章节。**写入前确认 CWD 在 worktree 内**。退出条件：6 维全 PASS（0 问题）。



    子代理输出异常时按 cross-review-matrix.md 失败处理策略执行（代码评审 3 轮上限）



14. **auto-verify**（AC-8，可选）：读取 `.flowgo-config` 中 `auto_verify` 配置（默认 false），若 true 则每完成子任务自动运行 `python3 references/scripts/gate_check.py --mode l1-guard --change-id <id> --specs-dir .specs/<id> --project-dir .`，失败则输出失败项 + 建议运行 `git stash`



15. **原子提交前终验**：`git branch --show-current` 确认 `change/<id>` + `git status --porcelain` 检查无主仓库路径的变更。终验通过后提交：格式 `<type>(<change-id>): <task-id> <subject>`（仅评审通过后）







**自调节机制**（借鉴 gstack）：



- **Blast radius check**：修复涉及 > 5 文件时，停下向用户确认范围



- **连续失败熔断**：编译/运行连续失败 3 次 → 停下报告用户，不盲目重试



- **改动文件上限**：单任务改动 > 10 文件时警告，建议拆分



- **Plateau 停滞检测**（stagnation_patience 控制，默认 3）：



  - 维护 `consecutive_failures` 计数器（在阶段进度中记录）



  - task verify 或 Guard 失败 → counter += 1；task 成功 → counter 重置为 0



  - counter >= stagnation_patience → 暂停，输出升级报告：



    ```



    ⚠️ Plateau 检测：连续 {N} 个 task 未能通过验证



    已尝试方法：{失败 task 的 action 摘要}



    推荐方向：{基于 git log 分析失败模式，建议 2-3 个替代方向}



    ```



  - 用户选择：(a) 调整策略后继续 (b) 跳过当前 task (c) 中断







**结构化迭代日志**（iteration_log 控制，默认 true）：



- 每个 task 完成后（无论成功或失败），追加一行到 `.specs/<id>/iterations.tsv`



- 格式：`{timestamp}\t3-开发\t{task_id}\t{action摘要}\t{status}\t{metric}\t{description}`



- 首次写入时先创建表头行



- 追加失败时降级告警，不阻塞 task 流程







**输出**：代码 + `.specs/<id>/<task-id>-SUMMARY.md`（含交叉评审章节）







**入口条件**：DESIGN.md + TASK.md（含 verify）+ `<change-id>-REVIEW.md`（任务评审 PASS）存在；指定任务时验证该任务存在且 depends_on 已完成







**完成条件**：verify 通过（0 失败） + 交叉评审 6 维全 PASS + SUMMARY 完成（无已知问题） + 代码已提交







**自检**：
- [ ] **步骤 0 worktree 验证已通过**（`git branch --show-current` = `change/<id>`，`pwd` 在 worktree 内）
- [ ] **步骤 9 提交前路径校验已通过**（所有变更文件在 worktree 内，无主仓库路径变更）
- [ ] **步骤 15 原子提交终验已通过**（`change/<id>` 分支确认，无主仓库路径残留）
- [ ] 锁文件已清理（SUMMARY 写完后 .lock 不存在）
- [ ] grep 沿用结果贴入 SUMMARY
- [ ] 交叉评审 6 维全 PASS（独立子代理确认）
- [ ] 没改 REQUIREMENT / DESIGN
- [ ] 评审未超过 3 轮（超过则已报告用户）
- [ ] 调试日志已清理（grep 无 [DEBUG- 残留）
- [ ] 调试假设已记录（在 SUMMARY 或 commit message 中）

**中断恢复**：



- **创建**：触发清窗信号时写 `<task-id>-PROGRESS.md`，更新 `.specs/<change-id>/STATE.md` 的 `中断任务` 字段



- **删除**：以下任一条件满足时删除：



  1. 任务完成（verify 通过 + 交叉评审 PASS + SUMMARY 写完）→ 原子提交前删除



  2. 任务被替换（用户要求重做）→ 创建新 PROGRESS 前删旧文件



  3. spec 归档时（归档流程步骤 6）→ 强制清理 spec 目录下所有 `*-PROGRESS.md`



- **校验**：STATE.md `中断任务` 清空前，确认对应 PROGRESS.md 已删除







**会话恢复入口**（用户说"go"时，路由到此阶段后自动触发）：

0. **执行步骤 0（Worktree 上下文验证）**：恢复上下文前必须先确认在 worktree 中。验证失败 → 重新 EnterWorktree。此步骤不可跳过——跨会话恢复是 CWD 丢失的高风险场景
1. 读 `<task-id>-PROGRESS.md`（如存在）→ 从记录的断点步骤继续
2. 读最近一个 `<task-id>-SUMMARY.md`（如存在）→ 了解上一个完成任务的上下文
3. 两者都不存在 → 从步骤 1（读任务定义）开始
4. 恢复时输出「📂 恢复上下文：T02，从 {断点步骤} 继续」







**决策信号**：



- 创建了新抽象（沿用搜索未找到→新建）



- 实现偏离 DESIGN.md



- 交叉评审经过 2+ 轮才通过（初始实现有质量问题）







**类型适配**（TASK.md type 属性决定开发策略）：



- bugfix：跳过步骤 2 策略复用（bug 模式不适用成功策略）；步骤 6 TDD 必须先写失败测试复现 bug；加强步骤 10 diff 边界检查



- feature：默认模式，完整开发流程



- refactor：步骤 6 TDD 重点在 REFACTOR 环（红绿阶段快速通过）；加强步骤 10 边界检查（重构应只改结构不改行为）



- doc：跳过步骤 6 TDD 和步骤 13 交叉评审；改为可读性自检（术语一致、示例可运行）



- config：跳过步骤 6 TDD；步骤 10 diff 边界检查加强（配置变更影响面大）；步骤 7 verify 必须包含配置语法验证



- chore：跳过步骤 6 TDD 和步骤 13 交叉评审；verify 改为效果验证命令







## 上下文需求清单







| 来源工件 | 字段 | 必选/可选 | 保留方式 |



|---------|------|---------|---------|



| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |



| REQUIREMENT.md | 范围排除 | 必选 | 原文保留 |



| REQUIREMENT.md | 原则 | 必选 | 原文保留 |



| DESIGN.md | 架构图 | 必选 | 原文保留 |



| DESIGN.md | API 设计 | 必选 | 原文保留 |



| TASK.md | 当前任务 | 必选 | 原文保留 |



| CONTEXT.md | 域语言 | 可选 | 压缩为一行 |



| CONTEXT.md | 禁止清单 | 必选 | 原文保留 |







## 反模式自检



对照 SKILL.md「3-开发 反模式」清单逐条自检。命中任一条即停止修正。







## 精炼环



代码编写完成后、写 SUMMARY 之前，执行 SKILL.md「阶段内精炼环」4 项检查。LITE 模式跳过。







**Git as Memory 扩展**（精炼环「边界卫生」项增强）：



- 运行 `git log --oneline -5`，检查最近 5 个 commit 消息



- 识别已回滚方案：消息含 `Revert` 或 `回滚` → 记录该方案为已失败



- 当前 task 的实现方向与已回滚方案重叠 → 输出「⚠️ 方案与已回滚的 {commit} 重叠，建议换方向」



- 识别成功模式：最近 3 个非 Revert commit → 提取共性文件/方法，优先沿用







## 验证闭环



精炼环通过后，执行 SKILL.md「阶段内验证闭环」开发场景 3 步。结果记录到 SUMMARY.md。



