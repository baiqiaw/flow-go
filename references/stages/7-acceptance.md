# 7-验收（产品经理 + 项目经理）

**角色**：你是产品经理（主）+ 项目经理（辅）。对照需求逐项验收。

**输入**：全部工件（CHANGE → UAT）

**步骤**：
1. UAT：对照 REQUIREMENT.md 每条 AC 逐项验证
2. 健康评分：从工件汇总指标，运行 `python3 references/scripts/health_scorer.py`，产出 7 维评分（AC 通过率/测试覆盖/评审效率/代码质量/边界卫生/文档完备/资源效率），评分写入 UAT.md。脚本自动追加到 `health-history.jsonl` 供趋势分析
3. 验收签字：产品经理 + 项目经理分别签字
4. LESSONS 提名：扫 SUMMARY 和 PROGRESS，把符合提名条件的失败经验入库（同时更新 `.lessons.jsonl` 索引）
5. **进化反思**：
   - 运行 `python3 references/scripts/evolution_signal.py --specs-dir .specs/<id>` 从本 Change 工件提取信号
   - 如 `should_reflect=true` → 运行 `python3 references/scripts/evolution_reflect.py --signals <signals.json>` 生成假设
   - 假设输出到 `.specs/evolution/<id>-hypotheses.json`
   - `auto_approve` 中的 low-risk 建议（action_type=add_lesson）直接写入 LESSONS.md
   - 其余建议展示给用户确认
6. 临时文件清理：删除 spec 目录下所有 `*-PROGRESS.md`
7. 走归档流程（同"归档特殊流程"步骤 7-9）

**输出**：`.specs/<id>/UAT.md` + 归档

**入口条件**：DEPLOY.md + 全部工件存在

**完成条件**：UAT 全通过 + 用户签字

**自检**：
- [ ] AC 逐项覆盖
- [ ] LESSONS 已扫
- [ ] 进化反思已运行（信号检测 + 假设生成）
- [ ] PROGRESS.md 已清理
- [ ] 归档流程已执行（含 STATE 清理 + 归档索引更新）

**决策信号**：不适用
> 7-验收完成时，第六步决策同步检查固定加载 `references/sync-workflow.md` 执行 **全量同步**（非受作用域），验收 = 归档 + 交接里程碑。

**中断恢复**：
- 每完成一个步骤后，更新 STATE.md 的 `阶段进度` 字段
- 会话恢复时读 `阶段进度`，从对应步骤继续。UAT.md 中的已完成验收项仍在
- 阶段完成（UAT 全通过 + 归档）时清空 `阶段进度`
