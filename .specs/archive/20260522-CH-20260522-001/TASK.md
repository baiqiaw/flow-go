# TASK — CH-20260522-001

## 依赖图

```
T01 ──→ T02
T03 (独立)
T04 (独立)
```

并行分组：T01 → T02（串行链）；T03、T04 可与 T01 并行。

---

## T01 — SKILL.md 权衡声明 + 锚点口诀 + 直觉检验

<task id="T01" priority="Must" mode="afk">
  <name>SKILL.md 增加权衡声明、角色声明锚点口诀、精炼环直觉检验</name>
  <read_files>
    SKILL.md
  </read_files>
  <write_files>
    SKILL.md
  </write_files>
  <action>
    1. 在 SKILL.md 的「流程全景」之后、「前置动作」之前，插入权衡声明块（2-3 行）：
       > **权衡声明**：flow-go 偏向严谨而非速度。LITE 模式可简化闸门，但涉及安全/跨模块/数据迁移的变更仍需完整流程。简单任务可酌情简化。

    2. 修改「第五步 · 角色声明」模板，在 `✅ 项目记忆` 之后增加一行：
       `✅ 阶段锚点：<对应当前阶段的口诀>`
       并在模板下方附上 8 阶段锚点口诀表：
       | 阶段 | 锚点口诀 |
       |------|---------|
       | 0-需求 | 不确定就问，不猜不假设 |
       | 1-设计 | 每个决策有替代方案 |
       | 2-任务 | 每个 task 可独立验证 |
       | 3-开发 | 每行改动追溯到需求 |
       | 4-测试 | 按验收标准写用例，不改实现 |
       | 5-审查 | 0 严重项才过关 |
       | 6-部署 | 部署前有回滚方案 |
       | 7-验收 | 逐条对照 AC 验收 |

    3. 在「阶段内精炼环」步骤 2（反模式清零）之后插入新步骤：
       `3. **直觉检验**：资深工程师看了会说"太复杂了"吗？→ 是则简化`
       后续步骤编号顺延（原步骤 3→4，原步骤 4→5）
  </action>
  <verify>
    grep -c '权衡声明' SKILL.md && grep -c '阶段锚点' SKILL.md && grep -c '直觉检验' SKILL.md
  </verify>
  <done>
    SKILL.md 包含权衡声明（在流程全景后）、角色声明模板含锚点行+口诀表、精炼环含直觉检验步骤
  </done>
  <depends_on></depends_on>
  <e2e_coverage>SKILL.md 头部→角色声明→精炼环 三个区域全部覆盖</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
</task>

---

## T02 — gate-rules.md 锚点引用

<task id="T02" priority="Should" mode="afk">
  <name>gate-rules.md §4 阶段反模式速查增加锚点口诀引用</name>
  <read_files>
    references/gate-rules.md
  </read_files>
  <write_files>
    references/gate-rules.md
  </write_files>
  <action>
    在 gate-rules.md 的「§4 阶段反模式速查 [antipattern]」章节的各个阶段反模式摘要后，
    为每个阶段追加其锚点口诀（格式：`> 锚点：<口诀>`）。
    口诀内容与 SKILL.md 中 T01 写入的 8 阶段口诀表一致。
  </action>
  <verify>
    grep -c '锚点' references/gate-rules.md
  </verify>
  <done>
    gate-rules.md §4 每个阶段反模式摘要后附有对应锚点口诀
  </done>
  <depends_on>T01</depends_on>
  <e2e_coverage>gate-rules.md §4 全部阶段覆盖</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
</task>

---

## T03 — 反模式实例对照文件

<task id="T03" priority="Must" mode="afk">
  <name>创建 references/anti-pattern-examples.md（6 组 ❌/✅ 代码对照）</name>
  <read_files>
    references/anti-patterns.md
  </read_files>
  <write_files>
    references/anti-pattern-examples.md
  </write_files>
  <action>
    创建 references/anti-pattern-examples.md，包含 6 组 ❌/✅ 实例对照：

    1. **scope-creep**（需求蔓延，对应 req-03）：
       场景：用户要求"加一个导出按钮"，AI 顺手加了格式选择、分页、权限校验
       ❌ 过度扩展（30 行） → ✅ 精确实现（5 行）

    2. **over-engineering**（过度工程，对应 dev-01）：
       场景：用户要求"计算折扣"，AI 搞了策略模式+工厂+配置
       ❌ 策略模式抽象（40 行） → ✅ 一个函数（3 行）

    3. **drive-by-refactor**（顺手重构，对应 dev-02）：
       场景：用户要求"修复空邮箱崩溃"，AI 顺手改了邮箱验证逻辑+用户名校验+注释
       ❌ 连带修改 25 行 → ✅ 只修崩溃点 3 行

    4. **skip-clarification**（跳过澄清，对应 req-06）：
       场景：用户说"搜索加个排序"，AI 直接按分数排序，未问排序规则
       ❌ 默认假设直接实现 → ✅ 先问清楚再动手

    5. **fake-verify**（验证造假，对应 dev-03）：
       场景：verify 步骤贴"通过"而非真实命令输出
       ❌ 手写"通过"文本 → ✅ 贴真实命令输出

    6. **weaken-failing**（弱化失败用例，对应 test-02）：
       场景：测试红了，改测试让它变绿而非修代码
       ❌ 修改测试断言 → ✅ 修复实现代码

    每组使用伪代码（不依赖特定语言），格式统一：场景描述 → ❌ 错误做法（含注释说明问题）→ ✅ 正确做法 → 关键差异总结。
  </action>
  <verify>
    test -f references/anti-pattern-examples.md && grep -c '❌' references/anti-pattern-examples.md
  </verify>
  <done>
    references/anti-pattern-examples.md 存在，包含 6 组 ❌/✅ 对照
  </done>
  <depends_on></depends_on>
  <e2e_coverage>覆盖 6 个高频反模式的实例化展示</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
</task>

---

## T04 — 归档成功指标

<task id="T04" priority="Should" mode="afk">
  <name>special-flows.md 归档流程增加 3 条成功指标</name>
  <read_files>
    references/stages/special-flows.md
  </read_files>
  <write_files>
    references/stages/special-flows.md
  </write_files>
  <action>
    在 special-flows.md 归档流程的 git commit 步骤之后、STATE.md 清理之前，
    插入成功指标输出步骤：

    > **成功指标**（归档完成时输出，供用户快速判断 flow-go 是否生效）：
    > 1. Diff 中无关改动行数是否减少？（对比上次归档 diff）
    > 2. 因假设错误导致的返工是否减少？（回顾本 change 是否有因猜测导致的返工）
    > 3. 澄清问题是否在实现前提出？（回顾需求/设计阶段的提问记录）

    格式简洁，3 个问句，用户回答即可评估。
  </action>
  <verify>
    grep -c '成功指标' references/stages/special-flows.md
  </verify>
  <done>
    special-flows.md 归档流程包含 3 条成功指标
  </done>
  <depends_on></depends_on>
  <e2e_coverage>归档流程步骤中增加成功指标检查点</e2e_coverage>
  <independently_verifiable>true</independently_verifiable>
</task>
