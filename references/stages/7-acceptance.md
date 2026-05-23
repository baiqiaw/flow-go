# 7-验收（产品经理 + 项目经理）

**角色**：你是产品经理（主）+ 项目经理（辅）。对照需求逐项验收。

**输入**：全部工件（CHANGE → UAT）

**步骤**：
1. UAT：对照 REQUIREMENT.md 每条 AC 逐项验证
1LV. **活体验证**：实际启动应用，按用户流程逐页测试，收集运行时证据
   - **1LV-1 项目类型检测**：扫描项目根目录特征文件（package.json / go.mod / Cargo.toml / setup.py），结合 TASK.md 中 verify 命令和 read_files 判断项目类型。判定结果：web / cli / library / unknown。结果追加到 UAT.md「活体验证」章节头部
   - **1LV-2 运行环境准备**：
     - web：尝试启动 dev server（npm run dev / go run 等），等待端口就绪。启动失败 → 询问用户是否安装依赖或手动启动。用户拒绝 → 跳过活体验证，记录原因到 UAT.md，转步骤 4
     - cli：无特殊准备
     - library：无特殊准备（走测试输出）
     - unknown → 询问用户项目类型，按用户回答走对应分支
   - **1LV-3 核心流程遍历**：从 REQUIREMENT.md 用户故事 + AC 提取用户流程
     - web 应用：检测 Playwright/browse 工具可用性。可用 → 逐页/逐路由自动测试，截图留证。不可用 → 输出手动测试指引清单，等用户反馈
     - cli 工具：bash 执行关键命令，校验 stdout/stderr/exit code
     - 纯库：运行测试套件，收集通过率和输出
   - **1LV-4 结果记录**：逐条写入 UAT.md 活体验证清单（LV-NN），格式：| LV-NN | 路径/操作 | 预期结果 | 实际结果 | 状态 | 证据 |。状态值：✅ 通过 / ❌ 失败（Critical/High）/ ⚠️ 部分通过（Low/Medium）。证据：截图路径 / 命令输出摘要 / 测试输出
   - **1LV-5 Bug 汇总判定**：统计 ❌ 条目，按严重度分类（Critical / High / Medium / Low）。Critical/High 合计 = 0 → 跳过步骤 1BF/1RR，直接进入步骤 4。Critical/High 合计 > 0 → 进入步骤 1BF（Bug 修复循环）
1BF. **Bug 修复循环**：活体验证发现 Critical/High 级别 bug 时，临时切换到开发员角色修复
   - **1BF-1 角色切换声明**：输出「🔧 角色切换：产品经理 → 开发员」。明确切换期间的开发员角色红线：最小修复（只改 bug 相关代码）、不改无关代码、不重构不优化、每个修复独立原子提交
   - **1BF-2 Bug 逐个修复（循环）**：按 Critical → High 优先级排序。对每个 bug：
     a. 定位源码：从 bug 描述 → TASK.md read_files → grep 搜索定位
     b. 最小修复：仅修改导致 bug 的代码路径
     c. 原子提交：fix(<change-id>): ISSUE-<N> — <简要描述>
     d. 回到 bug 位置重验：在活体验证环境中重新触发该操作
     e. 重验通过 → 标记 bug 状态为「已修复」
     f. 重验未通过 → 重新分析根因，再次修复（同一 bug 最多 3 次尝试，超过标记为「阻塞」跳过）
   - **1BF-3 自调节检查（每轮结束时执行）**：轮定义：所有已知 bug 遍历一轮 = 1 轮。检查条件：
     - Critical/High 合计 ≤ 0 → 退出循环
     - 连续 3 轮仍有 Critical/High → 触发停下报告
     - 单轮 Critical/High > 5 → 触发停下报告
     - 单个 bug 修复尝试 ≥ 3 次仍未解决 → 标记为「阻塞」，跳过该 bug
   - **1BF-4 停下报告（触发自调节阈值时）**：输出报告：触发原因、已修复/未修复统计、当前 bug 清单。3 个选项：继续修复（重置轮次计数器） / 回退到 3-开发阶段 / 记录已知问题并继续（带病验收）
   - **1BF-5 角色恢复声明**：输出「🔧 角色切换：开发员 → 产品经理」。进入步骤 1RR（验收重验）
1RR. **验收重验**：修复循环完成后全量重走核心流程
   - **1RR-1 全量重走核心流程**：重新执行步骤 1LV-3 的核心流程遍历。重点关注：修复的 bug 对应路径是否通过、修复是否引入新问题（回归检测）。结果追加到 UAT.md「验收重验」章节
   - **1RR-2 结果判定**：
     - 原 Critical/High bug 全部通过 → 验收重验通过
     - 发现新 Critical/High bug → 判定来源：新 bug 由修复引入 → 回到步骤 1BF（追加到 bug 清单）；新 bug 非修复引入 → 记录到 UAT.md，询问用户处理方式
     - 回到 1BF 的次数上限 = 2 次（超过则停下报告用户决策）
   - **1RR-3 完成记录**：UAT.md 追加验收重验总结：重验通过项 / 新发现问题 / 回归次数 / 最终 bug 状态汇总表
4. 健康评分：从工件汇总指标，运行 `python3 references/scripts/health_scorer.py`，产出 7 维评分（AC 通过率/测试覆盖/评审效率/代码质量/边界卫生/文档完备/资源效率），评分写入 UAT.md。脚本自动追加到 `health-history.jsonl` 供趋势分析
5. 验收签字：产品经理 + 项目经理分别签字
6. LESSONS 提名：扫 SUMMARY 和 PROGRESS，把符合提名条件的失败经验入库（同时更新 `.lessons.jsonl` 索引）
7. **进化反思**：
   - **对话反馈分类**（7a，在信号检测前执行）：运行 `python3 references/scripts/feedback_classifier.py --specs-dir .specs/<id> --output .specs/evolution/<id>-classified-feedback.json`，将 `.specs/<id>/user-inputs.jsonl` 中的用户输入分为 project/skill/preference/noise 四类。skill 反馈追加到 `.specs/evolution/skill-feedback.jsonl`。输出分类摘要。LITE 模式使用 `--complexity LITE` 降低灵敏度
   - 运行 `python3 references/scripts/evolution_signal.py --specs-dir .specs/<id>` 从本 Change 工件提取信号
   - 如 `should_reflect=true` → 运行 `python3 references/scripts/evolution_reflect.py --signals <signals.json>` 生成假设
   - 假设输出到 `.specs/evolution/<id>-hypotheses.json`
   - `auto_approve` 中的 low-risk 建议（action_type=add_lesson）直接写入 LESSONS.md
   - 其余建议展示给用户确认
8. 临时文件清理：删除 spec 目录下所有 `*-PROGRESS.md`
9. 走归档流程（同"归档特殊流程"步骤 7-9）
10. **全量同步**：加载 `references/sync-workflow.md` 执行全量同步（非受作用域）。验收 = 归档 + 交接里程碑，全量同步确保知识库与项目状态完全对齐。同步完成后输出变更摘要（记忆 / 文档 / 未处理三层）。此步骤不依赖 SKILL.md 第七步的信号检查，由验收阶段直接触发
11. 走归档流程（同"归档特殊流程"步骤 10-11），将步骤 9-10 的全部变更（含归档文件 + 同步产出的 CLAUDE.md/CONTEXT.md 等）纳入一次 git commit + push + clean 验证

**输出**：`.specs/<id>/UAT.md` + 归档 + 全量同步完成

**入口条件**：DEPLOY.md + 全部工件存在 + 应用可运行（可选，不阻塞，跳过时记录原因）

**完成条件**：UAT 全通过 + 活体验证全通过或已跳过并记录原因 + 用户签字 + 全量同步完成 + git 已 push 且 working tree clean

**自检**：
- [ ] AC 逐项覆盖
- [ ] 活体验证已执行或已跳过并记录原因
- [ ] 修复循环角色切换已完成（如适用）
- [ ] 验收重验已通过（如适用）
- [ ] LESSONS 已扫
- [ ] 进化反思已运行（信号检测 + 假设生成）
- [ ] PROGRESS.md 已清理
- [ ] 归档流程已执行（含 STATE 清理 + 归档索引更新）
- [ ] 全量同步已执行（加载 sync-workflow.md，输出变更摘要）
- [ ] 归档 git commit + push 已完成（含同步产出的文件变更）

**决策信号**：验收完成固定触发全量同步（步骤 10 已内联执行，不依赖 SKILL.md 第七步信号检查）

**中断恢复**：
- 每完成一个步骤后，更新 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段
- 会话恢复时读 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段，从对应步骤继续。UAT.md 中的已完成验收项和活体验证结果仍在
- 阶段完成（UAT 全通过 + 归档）时清空 `阶段进度`

## 上下文需求清单

| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |
| CHANGE.md | 验收线 + 范围排除 | 必选 | 原文保留 |
| DEPLOY.md | 全部 | 必选 | 原文保留 |
| DESIGN.md | 步骤详细设计（1LV/1BF/1RR） | 必选 | 原文保留 |
| TASK.md | read_files / verify | 必选 | 压缩为文件列表 |
