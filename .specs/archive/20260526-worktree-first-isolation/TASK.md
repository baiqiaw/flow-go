# TASK — worktree-first-isolation

## 依赖图

```
T01 ──→ T05 ──→ T06
T02 ──→ T05
T03 ──→ T05
T04 ──→ T05

T01/T02/T03/T04 可并行（无互相依赖）
T05 依赖 T01-T04（所有改动完成后统一测试）
T06 依赖 T05（测试通过后交叉评审）
```

## 并行分组

- 组 A [并行]：T01(small) + T02(small) + T03(small) + T04(small) — 各自独立文件改动
- 串行：T05(medium) — 全量回归测试
- 串行：T06(medium) — 交叉评审

## 任务列表

<task id="T01" parallel="true" priority="must" type="feature" mode="afk">
  <name>SKILL.md 第一步+第七步+横切关注点重写</name>
  <read_files>SKILL.md</read_files>
  <write_files>SKILL.md</write_files>
  <action>修改 SKILL.md：(1) 第一步（读状态）用 git worktree list --porcelain 替代索引表解析，删除旧格式检测与迁移逻辑；(2) 横切关注点中 change_id 获取改为从 worktree 路径推导；(3) 第七步状态更新移除索引表操作（添加/移除索引行），改为 worktree 创建/清理</action>
  <verify>grep -c '索引表\|parse.*index\|活跃 Change.*表\|活跃数' SKILL.md → 结果为 0; grep -c 'worktree_path\|worktree.*推导' SKILL.md → 结果 ≥ 1</verify>
  <done>SKILL.md 中无索引表相关逻辑，第一步用 git worktree list 发现活跃 change，横切关注点 change_id 从 worktree 路径推导，第七步无索引表更新</done>
  <guard>grep -c 'worktree list' SKILL.md → 结果 ≥ 1</guard>
  <depends_on></depends_on>
  <e2e_coverage>启动路由 → 状态更新 全链路</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>改动集中在 SKILL.md 一个文件，约 60 行修改</agent_hint>
</task>

<task id="T02" parallel="true" priority="must" type="feature" mode="afk">
  <name>0-requirement.md 新增步骤 3.5 + 2-task.md 移除步骤 0</name>
  <read_files>references/stages/0-requirement.md, references/stages/2-task.md</read_files>
  <write_files>references/stages/0-requirement.md, references/stages/2-task.md</write_files>
  <action>(1) 0-requirement.md 步骤 3 后新增步骤 3.5"Worktree 创建"：EnterWorktree 创建 change/<id> 分支 + cwd 切换 + .specs/<id>/ 目录创建 + STATE.md worktree_path 写入，含 Bash 回退路径（git worktree add + cd）；(2) 2-task.md 移除步骤 0 的完整 worktree 创建逻辑（约 10 行），保留 worktree 验证（确认 worktree_path 非空）</action>
  <verify>grep -n '3\.5.*Worktree' references/stages/0-requirement.md → 有匹配; grep -c 'EnterWorktree' references/stages/2-task.md → 结果为 0</verify>
  <done>0-requirement.md 有步骤 3.5 完整 worktree 创建逻辑，2-task.md 步骤 0 已移除</done>
  <depends_on></depends_on>
  <e2e_coverage>需求阶段 → 任务阶段 worktree 创建交接</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>两个文件改动独立，但逻辑关联，合并为一个 task</agent_hint>
</task>

<task id="T03" parallel="true" priority="must" type="feature" mode="afk">
  <name>special-flows.md 归档拆分 + 特殊流程索引表清理 + commit 断言</name>
  <read_files>references/stages/special-flows.md</read_files>
  <write_files>references/stages/special-flows.md</write_files>
  <action>(1) 归档流程拆分：步骤 1-7 在 worktree 内执行（SUMMARY/PROGRESS/目录移动/commit），步骤 8-12 在 main 中执行（merge + 全局文件追加 + worktree 清理）；(2) 6 个特殊流程的索引表引用替换为 worktree 操作（按 DESIGN.md 映射表：热修→worktree list、中断→保留 worktree、并行→新 worktree、废弃→ExitWorktree remove、回溯→worktree list）；(3) 归档 commit 前新增完整性断言 test ! -d .specs/<id>；(4) commit message 规范增加 change-id 关联</action>
  <verify>grep -c '索引表' references/stages/special-flows.md → 结果为 0; grep -c 'worktree' references/stages/special-flows.md → 结果 ≥ 10</verify>
  <done>归档流程拆分为 worktree 内 + main 两阶段，所有索引表引用已替换为 worktree 操作，commit 前有断言</done>
  <depends_on></depends_on>
  <e2e_coverage>归档全流程（worktree → main → 清理）</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>改动量最大（~80 行），但逻辑清晰，按 DESIGN 映射表逐条替换</agent_hint>
</task>

<task id="T04" parallel="true" priority="must" type="feature" mode="afk">
  <name>validate_state.py 重写 + meta-artifacts.md 模板 + pipeline-continuation.md 清理</name>
  <read_files>references/scripts/validate_state.py, references/artifacts/meta-artifacts.md, references/common/pipeline-continuation.md</read_files>
  <write_files>references/scripts/validate_state.py, references/artifacts/meta-artifacts.md, references/common/pipeline-continuation.md</write_files>
  <action>(1) validate_state.py：删除 parse_change_ids_from_index()、detect_legacy_format()、PROJECT_REQUIRED_FIELDS 索引表字段；新增 discover_active_changes() 函数（调用 git worktree list --porcelain 解析 change/* 分支）；重写 validate() 主函数（用 worktree list 替代索引表校验）；保留 validate_change_state() 不变；(2) meta-artifacts.md：STATE.md 模板移除索引表，简化为"由 git worktree list 管理"，移除一致性约束和旧格式迁移章节；(3) pipeline-continuation.md：移除"STATE.md 索引表新增该 change 行"</action>
  <verify>grep -c 'parse_change_ids_from_index\|detect_legacy_format\|索引表' references/scripts/validate_state.py → 结果为 0; grep -c 'discover_active_changes' references/scripts/validate_state.py → 结果 ≥ 1; grep -c '索引表' references/artifacts/meta-artifacts.md → 结果为 0; grep -c '索引表' references/common/pipeline-continuation.md → 结果为 0</verify>
  <done>validate_state.py 无索引表逻辑，有 worktree list 发现函数；meta-artifacts.md 模板无索引表；pipeline-continuation.md 无索引表操作</done>
  <depends_on></depends_on>
  <e2e_coverage>状态校验全链路（worktree 发现 → per-change 校验）</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>small</context_budget>
  <agent_hint>validate_state.py 是唯一 Python 改动，meta-artifacts 和 pipeline-continuation 是轻量清理</agent_hint>
</task>

<task id="T05" parallel="false" priority="must" type="feature" mode="afk">
  <name>测试用例重写 + 全量回归测试</name>
  <read_files>tests/test_scripts.py, references/scripts/validate_state.py</read_files>
  <write_files>tests/test_scripts.py</write_files>
  <action>(1) 重写 TestValidateState 的 4 个测试用例：test_valid_state 改为测试无索引表格式（mock git worktree list 返回），test_empty_state_file 保留，test_missing_fields 改为测试 Pipeline 待续+更新时间字段缺失，test_stage_mismatch 改为测试 worktree 存在但 per-change STATE.md 阶段异常；(2) 新增 test_discover_active_changes 测试 worktree list 解析；(3) 新增 test_backward_compat_archive 测试旧归档 STATE.md 可读；(4) 安装 pytest（source venv）后运行 pytest tests/ 确认全部通过</action>
  <verify>cd /home/cgh/projects/flow-go && source /mnt/c/Users/45079/venv/bin/activate && pytest tests/ -v 2>&1 | tail -5</verify>
  <done>所有测试通过（含重写的 TestValidateState + 新增测试），gate_check.py 相关测试无回归</done>
  <depends_on>T01, T02, T03, T04</depends_on>
  <e2e_coverage>全量回归</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>medium</context_budget>
  <agent_hint>依赖所有改动完成，需 mock git worktree list 输出</agent_hint>
</task>

<task id="T06" parallel="false" priority="must" type="feature" mode="colab">
  <name>交叉评审（任务阶段）</name>
  <read_files>.specs/worktree-first-isolation/TASK.md, .specs/worktree-first-isolation/DESIGN.md, .specs/worktree-first-isolation/REQUIREMENT.md</read_files>
  <write_files>.specs/worktree-first-isolation/worktree-first-isolation-REVIEW.md</write_files>
  <action>dispatch 交叉评审子代理，评审 TASK.md 的 6 维矩阵。任一维度 FAIL → 修 TASK → 重评。6 维全 PASS → 完成</action>
  <verify>grep -c 'PASS' .specs/worktree-first-isolation/worktree-first-isolation-REVIEW.md → 结果 ≥ 6</verify>
  <done>TASK.md 交叉评审 6 维全 PASS</done>
  <depends_on>T05</depends_on>
  <e2e_coverage>任务拆解质量验证</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
  <context_budget>medium</context_budget>
  <agent_hint>交叉评审需人工确认评审报告</agent_hint>
</task>
