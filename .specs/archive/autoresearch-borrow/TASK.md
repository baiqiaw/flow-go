# TASK — autoresearch-borrow

## 依赖图
T01 → T02 → T03 → T04（顺序执行，共享 3-develop.md）

## 任务列表

<task id="T01" parallel="false" priority="must" type="feature" mode="colab">
  <name>Guard 机制实现</name>
  <read_files>
    SKILL.md,
    references/stages/3-develop.md,
    references/artifacts/task-artifacts.md
  </read_files>
  <write_files>
    SKILL.md,
    references/stages/3-develop.md,
    references/artifacts/task-artifacts.md
  </write_files>
  <action>
1. SKILL.md 配置表新增 guard_enabled（默认 true）和 guard_timeout（默认 30）
2. task-artifacts.md TASK 模板新增可选 `<guard>` 字段，TASK 自检增加 guard 相关项
3. 3-develop.md 步骤 9（verify）后新增 Guard 执行步骤：读取 task guard 字段→执行→通过继续→失败回滚→超时告警
  </action>
  <verify>grep -c "guard_enabled\|guard_timeout\|<guard>" SKILL.md references/stages/3-develop.md references/artifacts/task-artifacts.md</verify>
  <done>SKILL.md 有 guard 配置项、task-artifacts.md 有 guard 字段、3-develop.md 有 Guard 执行步骤</done>
  <depends_on></depends_on>
  <e2e_coverage>SKILL.md 配置表 → 3-develop.md 步骤 9a → task-artifacts.md 模板字段</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
</task>

<task id="T02" parallel="false" priority="must" type="feature" mode="colab">
  <name>Git as Memory 实现</name>
  <read_files>
    SKILL.md,
    references/stages/special-flows.md,
    references/stages/3-develop.md
  </read_files>
  <write_files>
    SKILL.md,
    references/stages/special-flows.md,
    references/stages/3-develop.md
  </write_files>
  <action>
1. SKILL.md 配置表新增 git_memory_depth（默认 20）
2. special-flows.md 回溯流程步骤 1 后新增步骤 1.7：读取 git log --oneline -{depth} + 最近 3 commit 的 diff --stat 摘要，注入会话上下文
3. 3-develop.md 精炼环「边界卫生」项扩展：新增 git log 最近 5 commit 检查，识别已回滚方案（DESIGN §5 定义的重叠判定规则），避免重复
  </action>
  <verify>grep -c "git log\|git_memory_depth\|Git as Memory" references/stages/special-flows.md references/stages/3-develop.md</verify>
  <done>回溯流程读取 git 历史、精炼环检查 git 避免重复方案</done>
  <depends_on>T01</depends_on>
  <e2e_coverage>SKILL.md 配置 → special-flows.md 回溯 → 3-develop.md 精炼环</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
</task>

<task id="T03" parallel="false" priority="must" type="feature" mode="colab">
  <name>Plateau 停滞检测实现</name>
  <read_files>
    SKILL.md,
    references/stages/3-develop.md,
    references/stages/4-test.md
  </read_files>
  <write_files>
    SKILL.md,
    references/stages/3-develop.md,
    references/stages/4-test.md
  </write_files>
  <action>
1. SKILL.md 配置表新增 stagnation_patience（默认 3）
2. 3-develop.md 自调节机制区域新增 Plateau 检测：追踪连续失败 task 数（DESIGN §3 定义的计数器和升级报告格式），达阈值输出升级报告并暂停等用户决策
3. 4-test.md 自调节机制区域新增 Plateau 告警：连续 N 轮修复无改善时输出停滞告警（不暂停，仅建议）
  </action>
  <verify>grep -c "stagnation_patience\|Plateau\|停滞" SKILL.md references/stages/3-develop.md references/stages/4-test.md</verify>
  <done>SKILL.md 有配置项、3-develop.md 和 4-test.md 有停滞检测逻辑</done>
  <depends_on>T02</depends_on>
  <e2e_coverage>SKILL.md 配置 → 3-develop.md 停滞检测 → 4-test.md 停滞告警</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
</task>

<task id="T04" parallel="false" priority="must" type="feature" mode="colab">
  <name>结构化迭代日志实现</name>
  <read_files>
    SKILL.md,
    references/stages/3-develop.md,
    references/stages/4-test.md
  </read_files>
  <write_files>
    SKILL.md,
    references/stages/3-develop.md,
    references/stages/4-test.md
  </write_files>
  <action>
1. SKILL.md 配置表新增 iteration_log（默认 true）
2. 3-develop.md 步骤 14（原子提交）后新增 TSV 追加步骤：完成 task 后按 DESIGN §4 定义的格式追加到 .specs/<id>/iterations.tsv
3. 4-test.md 步骤 8 后新增 TSV 追加步骤：每轮测试完成后按同格式追加
  </action>
  <verify>grep -c "iterations.tsv\|iteration_log" SKILL.md references/stages/3-develop.md references/stages/4-test.md</verify>
  <done>SKILL.md 有配置项、3-develop.md 和 4-test.md 有 TSV 追加步骤</done>
  <depends_on>T03</depends_on>
  <e2e_coverage>SKILL.md 配置 → 3-develop.md TSV 追加 → 4-test.md TSV 追加</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
</task>
