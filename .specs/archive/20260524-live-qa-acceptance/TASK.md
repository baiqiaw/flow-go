# TASK — live-qa-acceptance

## 依赖图
T01(UAT 模板) / T02(验收步骤) / T03(闸门规则) 三者修改不同文件，无依赖，全部可并行。

T01 → AC-6
T02 → AC-1, AC-2, AC-3, AC-4, AC-5
T03 → AC-7, AC-8

## 并行分组（预检环生成）
- 组 A [并行]：T01(small) + T03(small) — 纯模板/闸门文本修改，可共享执行
- 组 B：T02(medium) — 步骤定义主体，独立执行

## 任务列表

<task id="T01" parallel="true" priority="must" type="feature" mode="afk">
  <name>更新 UAT.md 模板，增加活体验证和验收重验章节</name>
  <read_files>
    references/artifacts/deploy-artifacts.md
    .specs/live-qa-acceptance/DESIGN.md（UAT.md 模板变更章节）
  </read_files>
  <write_files>references/artifacts/deploy-artifacts.md</write_files>
  <action>
在 deploy-artifacts.md 的 UAT.md 模板中，在 `## 验收脚本` 示例结束之后、`## 健康评分` 之前，插入 2 个新章节：

1. `## 活体验证` — 含项目类型/验证方式/应用状态 3 个元数据字段 + `### 活体验证清单`（LV-NN 表格：编号/路径操作/预期结果/实际结果/状态/证据）+ `### Bug 清单`（ISSUE-NN 表格：编号/描述/类别/严重度/状态/修复提交）
2. `## 验收重验` — 含重验次数/最终结果元数据 + RR-NN 表格（编号/路径操作/预期/实际/状态）

插入后模板章节完整顺序：验收脚本 → 活体验证 → 验收重验 → 健康评分 → 验收签字 → LESSONS 提名 → 归档

具体 markdown 模板内容从 DESIGN.md「UAT.md 模板变更」章节复制。
  </action>
  <verify>grep -c "## 活体验证" references/artifacts/deploy-artifacts.md && grep -c "## 验收重验" references/artifacts/deploy-artifacts.md && grep -c "Bug 清单" references/artifacts/deploy-artifacts.md</verify>
  <done>deploy-artifacts.md 的 UAT 模板包含活体验证（含 LV-NN 清单和 Bug 清单）和验收重验（含 RR-NN 表格）两个新章节，位于验收脚本之后、健康评分之前</done>
  <depends_on></depends_on>
  <e2e_coverage>模板章节 → 7-acceptance.md 步骤引用 → UAT.md 产出</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>纯模板文本插入，从 DESIGN.md 复制即可</agent_hint>
</task>

<task id="T02" parallel="true" priority="must" type="feature" mode="afk">
  <name>更新 7-acceptance.md，增加活体验证/修复循环/验收重验步骤</name>
  <read_files>
    references/stages/7-acceptance.md
    .specs/live-qa-acceptance/DESIGN.md（步骤详细设计章节）
    .specs/live-qa-acceptance/REQUIREMENT.md（AC-1~AC-5）
  </read_files>
  <write_files>references/stages/7-acceptance.md</write_files>
  <action>
修改 7-acceptance.md，按 DESIGN.md 步骤插入架构执行：

1. 在现有步骤 1（UAT）之后，插入 3 个新步骤：
   - 步骤 1LV 活体验证（含 1LV-1~1LV-5 子步骤，覆盖 AC-1 活体验证 + AC-2 不可运行场景）
   - 步骤 1BF Bug 修复循环（含 1BF-1~1BF-5 子步骤，覆盖 AC-3 修复循环 + AC-4 自调节）
   - 步骤 1RR 验收重验（含 1RR-1~1RR-3 子步骤，覆盖 AC-5 验收重验）
   每个步骤的具体内容从 DESIGN.md「步骤详细设计」章节复制。

2. 将原步骤 2-9 重编号为步骤 4-11

3. 更新自检清单：追加「活体验证已执行或已跳过并记录」「修复循环角色切换已完成」「验收重验已通过」

4. 更新入口条件：追加「应用可运行（可选，不阻塞，跳过时记录原因）」

5. 更新完成条件：追加「活体验证全通过或已跳过并记录原因」

6. 更新上下文需求清单：追加 DESIGN.md 步骤设计章节

7. 更新中断恢复描述：步骤编号与新增步骤一致
  </action>
  <verify>grep -c "步骤 1LV\|步骤 1BF\|步骤 1RR" references/stages/7-acceptance.md && grep -c "活体验证已执行或已跳过" references/stages/7-acceptance.md</verify>
  <done>7-acceptance.md 包含 1LV/1BF/1RR 三个新步骤（含完整子步骤），原步骤已重编号，自检/入口/完成/上下文/中断恢复均已更新</done>
  <depends_on></depends_on>
  <e2e_coverage>步骤定义 → 模板章节(UAT.md) → 实际验收产出</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>medium</context_budget>
  <agent_hint>最大任务，从 DESIGN.md 复制步骤设计，注意保持与现有步骤格式一致</agent_hint>
</task>

<task id="T03" parallel="true" priority="must" type="feature" mode="afk">
  <name>更新 gate-rules.md，修改 7-验收闸门条件</name>
  <read_files>
    references/gate-rules.md
    .specs/live-qa-acceptance/DESIGN.md（闸门规则变更章节）
  </read_files>
  <write_files>references/gate-rules.md</write_files>
  <action>
修改 gate-rules.md 中 7-验收 的闸门条件，覆盖完整/最短/增量 3 条路径：

1.1 完整路径（§1.1）7-验收行：
  - 入口条件追加「应用可运行（可选，不阻塞，跳过时记录原因）」
  - 完成条件追加「活体验证全通过或已跳过并记录原因」

1.2 最短路径（§1.2）7-验收行：
  - 入口条件追加「应用可运行（可选）」
  - 完成条件改为「活体验证全通过或已跳过并记录原因」

1.3 增量路径（§1.3）7-验收行：
  - 入口条件追加「应用可运行（可选）」
  - 完成条件追加「活体验证全通过或已跳过并记录原因」

具体修改文本从 DESIGN.md「闸门规则变更」章节复制。
  </action>
  <verify>grep -c "活体验证全通过或已跳过" references/gate-rules.md && ! grep -q "7-验收.*入口条件\|7-验收.*完成条件" SKILL.md</verify>
  <done>gate-rules.md 3 条路径的 7-验收入口/完成条件均已追加活体验证条款；AC-8 通过 gate-rules.md 间接满足，SKILL.md 已确认无 7-验收条件硬编码文本</done>
  <depends_on></depends_on>
  <e2e_coverage>闸门条件 → SKILL.md 闸门检查引用 → 阶段转换验证</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>3 行文本修改，最小任务</agent_hint>
</task>
