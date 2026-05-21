# TASK — worktree-isolation

## 依赖图

```
T01 [P] ──┬──→ T03 [P]
          ├──→ T04 [P]
T02 [P] ──┘──→ T05 [P]
```

并行分组：
- Group A（基础层）：T01 + T02 可并行
- Group B（集成层）：T03 + T04 + T05 依赖 T01 完成后可并行

---

<task>
<id>T01</id>
<name>新建 worktree-lifecycle.md 生命周期定义</name>
<type>config</type>
<priority>Must</priority>
<read_files>
/home/cgh/.claude/skills/flow-go/SKILL.md
/home/cgh/.claude/skills/flow-go/references/stages/special-flows.md
</read_files>
<write_files>
/home/cgh/.claude/skills/flow-go/references/worktree-lifecycle.md
</write_files>
<action>
新建 `references/worktree-lifecycle.md`，定义完整的 worktree 生命周期。包含以下章节：

1. **概述**：worktree 隔离机制的目的和适用范围
2. **生命周期状态**：none → active → suspended → cleaned 四种状态的转换条件和判定方式
3. **创建流程**（对应 AC-1）：
   - 触发时机：2-任务闸门通过后
   - 操作步骤：EnterWorktree 创建 .claude/worktrees/<id> 分支 change/<id>
   - STATE.md 更新：per-change STATE.md 写入 worktree_path
   - 回退方案：EnterWorktree 不可用时用 Bash 执行 git worktree add
4. **活跃工作**（对应 AC-2）：
   - agent 在 worktree 中操作，所有改动提交到 change/<id> 分支
   - per-change STATE.md 在 worktree 内更新
5. **归档合并流程**（对应 AC-3、AC-4、AC-6）：
   - ExitWorktree 退出
   - git checkout main && git merge change/<id>
   - STATE.md 冲突处理：保留 main 版本，agent 手动移除已归档 change 行
   - git worktree remove .claude/worktrees/<id>
   - git branch -d change/<id>
6. **废弃清理流程**（对应 AC-5、AC-6）：
   - ExitWorktree 退出
   - git worktree remove --force .claude/worktrees/<id>
   - git branch -D change/<id>（不合并）
7. **中断处理**：
   - worktree 保留不删除，状态标记为 suspended
   - per-change STATE.md 保留 worktree_path
8. **回溯恢复**（对应 AC-7）：
   - 读取 per-change STATE.md 的 worktree_path
   - worktree_path 非空 → EnterWorktree 进入
   - worktree 不存在但路径有记录 → 提示用户 worktree 已丢失，需手动恢复
</action>
<verify>test -f /home/cgh/.claude/skills/flow-go/references/worktree-lifecycle.md && grep -c "创建流程\|归档合并\|废弃清理\|回溯恢复" /home/cgh/.claude/skills/flow-go/references/worktree-lifecycle.md | xargs -I{} sh -c '[ {} -ge 4 ] && echo "PASS: 4 个核心流程已定义" || echo "FAIL: 缺少核心流程定义"'</verify>
<done>references/worktree-lifecycle.md 已创建，包含完整的 4 种生命周期流程定义</done>
<depends_on></depends_on>
<context_budget>medium</context_budget>
<agent_hint>参考 SKILL.md 的步骤 1/3/7 理解状态管理上下文，参考 special-flows.md 理解归档/废弃/中断/回溯流程</agent_hint>
</task>

<task>
<id>T02</id>
<name>STATE.md schema 增加 worktree_path 字段</name>
<type>config</type>
<priority>Should</priority>
<read_files>
/home/cgh/.claude/skills/flow-go/references/artifacts/meta-artifacts.md
</read_files>
<write_files>
/home/cgh/.claude/skills/flow-go/references/artifacts/meta-artifacts.md
</write_files>
<action>
修改 `references/artifacts/meta-artifacts.md` 的 Change 级详情 Schema 表格：
1. 在 `阶段进度` 和 `更新时间` 之间新增 `worktree_path` 字段行：
   - 必填：否
   - 格式：`<路径>` 或 `无`
   - 默认值：`无`
   - 说明：worktree 目录的绝对路径。非空时表示该 change 有活跃 worktree。创建时写入，归档/废弃/清理后清为 `无`
2. 在格式约束中增加一条：`worktree_path 非空时，路径必须指向一个有效的 git worktree 目录`
</action>
<verify>grep "worktree_path" /home/cgh/.claude/skills/flow-go/references/artifacts/meta-artifacts.md | grep -c "必填" | xargs -I{} sh -c '[ {} -ge 1 ] && echo "PASS: worktree_path 字段已加入 schema" || echo "FAIL: 字段未找到"'</verify>
<done>meta-artifacts.md 的 Change 级 STATE schema 已包含 worktree_path 字段</done>
<depends_on></depends_on>
<context_budget>small</context_budget>
<agent_hint>仅修改 schema 表格和格式约束，不改动其他章节</agent_hint>
</task>

<task>
<id>T03</id>
<name>SKILL.md 增加 worktree 感知</name>
<type>config</type>
<priority>Must</priority>
<read_files>
/home/cgh/.claude/skills/flow-go/SKILL.md
/home/cgh/.claude/skills/flow-go/references/worktree-lifecycle.md
</read_files>
<write_files>
/home/cgh/.claude/skills/flow-go/SKILL.md
</write_files>
<action>
修改 SKILL.md 的 3 个步骤，增加 worktree 感知逻辑：

**步骤 1（读状态）修改**：
- 在"选定 change 后检查"段落（当前第 5 点）之后，增加 worktree 检查：
  "读取 `.specs/<id>/STATE.md` 的 `worktree_path` 字段。非空 → 检查 worktree 目录是否存在（`test -d <path>`）。存在 → 记录到会话上下文。不存在但路径有记录 → 输出「⚠️ worktree 已丢失：<path>，建议手动恢复或废弃」"

**步骤 3（意图路由）修改**：
- 在路由表之后、"第三步半"之前，增加 worktree 进入逻辑：
  "路由确定后，检查目标 change 的 worktree_path。非空且 worktree 存在 → 调用 EnterWorktree 进入 worktree。为空 → 留在主仓库（阶段 0-1 不需要 worktree）"

**步骤 7（状态更新）修改**：
- 在"阶段转换"条目后增加：
  "worktree 创建时：per-change STATE.md 的 `worktree_path` 写入路径值。归档/废弃清理后：`worktree_path` 清为 `无`"

**第六步（加载执行）修改**：
- 加载映射表增加一行：`worktree 生命周期 | grep 加载 references/worktree-lifecycle.md | —`
</action>
<verify>grep -c "worktree" /home/cgh/.claude/skills/flow-go/SKILL.md | xargs -I{} sh -c '[ {} -ge 3 ] && echo "PASS: SKILL.md 已包含 worktree 逻辑（{} 处引用）" || echo "FAIL: worktree 引用不足"'</verify>
<done>SKILL.md 的步骤 1/3/6/7 已增加 worktree 感知逻辑</done>
<depends_on>T01</depends_on>
<context_budget>medium</context_budget>
<agent_hint>SKILL.md 是 flow-go 的主文件，修改时保持现有结构不变，仅在对应步骤的段落内追加内容。不要重构或重排现有段落。</agent_hint>
</task>

<task>
<id>T04</id>
<name>2-task.md 闸门后增加 worktree 创建步骤</name>
<type>config</type>
<priority>Must</priority>
<read_files>
/home/cgh/.claude/skills/flow-go/references/stages/2-task.md
/home/cgh/.claude/skills/flow-go/references/worktree-lifecycle.md
</read_files>
<write_files>
/home/cgh/.claude/skills/flow-go/references/stages/2-task.md
</write_files>
<action>
修改 `references/stages/2-task.md`：

1. 在"步骤"列表的开头（步骤 1 之前），新增"步骤 0：Worktree 创建"：
   "0. **Worktree 创建**（如 per-change STATE.md 的 `worktree_path` 为 `无`）：
      - (a) 调用 EnterWorktree（name: <change-id>），创建分支 `change/<id>` 的 worktree
      - (b) 进入 worktree 后，更新 `.specs/<id>/STATE.md` 的 `worktree_path` 为 worktree 绝对路径
      - (c) worktree_path 已有值 → 跳过（已在 worktree 中）
      - (d) EnterWorktree 不可用 → 回退到 Bash：`git worktree add .claude/worktrees/<id> -b change/<id>` + `cd .claude/worktrees/<id>`"

2. 更新原步骤编号（1→1, 但插入的步骤 0 不影响后续编号——实际上应重新编号后续步骤为 1~10，步骤 0 变为步骤 0）

3. 自检清单增加一项：`[ ] worktree_path 已更新（如适用）`
</action>
<verify>grep -c "worktree" /home/cgh/.claude/skills/flow-go/references/stages/2-task.md | xargs -I{} sh -c '[ {} -ge 2 ] && echo "PASS: 2-task.md 已包含 worktree 创建步骤" || echo "FAIL: 未找到 worktree 引用"'</verify>
<done>2-task.md 已在闸门后增加 worktree 创建步骤（步骤 0）</done>
<depends_on>T01</depends_on>
<context_budget>small</context_budget>
<agent_hint>仅在步骤列表开头插入新步骤，不修改后续步骤内容。参考 worktree-lifecycle.md 的创建流程章节。</agent_hint>
</task>

<task>
<id>T05</id>
<name>special-flows.md 增加 worktree 处理逻辑</name>
<type>config</type>
<priority>Must</priority>
<read_files>
/home/cgh/.claude/skills/flow-go/references/stages/special-flows.md
/home/cgh/.claude/skills/flow-go/references/worktree-lifecycle.md
</read_files>
<write_files>
/home/cgh/.claude/skills/flow-go/references/stages/special-flows.md
</write_files>
<action>
修改 `references/stages/special-flows.md` 的 4 个流程：

**归档流程**修改：
- 步骤 3（归档原因确认）之后插入步骤 3.5："Worktree 合并：读取 per-change STATE.md 的 worktree_path。非空 → (a) ExitWorktree 退出 worktree (b) git checkout main (c) git merge change/<id>，STATE.md 冲突保留 main 版本 (d) git worktree remove <path> (e) git branch -d change/<id> (f) per-change STATE.md 的 worktree_path 清为 `无`。为空 → 跳过"
- 自检清单增加：`[ ] worktree 已合并并清理（如适用）`

**废弃流程**修改：
- 步骤 4（临时文件清理）之后插入步骤 4.5："Worktree 清理：读取 per-change STATE.md 的 worktree_path。非空 → (a) ExitWorktree (b) git worktree remove --force <path> (c) git branch -D change/<id>（不合并）。为空 → 跳过"
- 自检清单增加：`[ ] worktree 已清理（如适用）`

**中断流程**修改：
- 步骤 4（STATE.md 更新）中，更新内容增加："worktree_path 保持不变（worktree 保留，供恢复时重入）"
- 步骤 5（恢复提示）追加："如 worktree_path 非空，提示「worktree 保留在 <path>，恢复时将自动进入」"

**回溯流程**修改：
- 步骤 1 之后增加 worktree 重入逻辑："读取目标 change 的 worktree_path。非空且 worktree 目录存在 → EnterWorktree 进入。非空但目录不存在 → 输出「⚠️ worktree 已丢失：<path>」"
</action>
<verify>grep -c "worktree" /home/cgh/.claude/skills/flow-go/references/stages/special-flows.md | xargs -I{} sh -c '[ {} -ge 8 ] && echo "PASS: special-flows.md 已包含 worktree 处理（{} 处引用）" || echo "FAIL: worktree 引用不足（{} 处）"'</verify>
<done>special-flows.md 的归档/废弃/中断/回溯 4 个流程已增加 worktree 处理逻辑</done>
<depends_on>T01</depends_on>
<context_budget>medium</context_budget>
<agent_hint>修改 special-flows.md 时，每个流程（归档/废弃/中断/回溯）独立修改，不交叉影响。保持现有的步骤编号规则（使用 X.5 插入新步骤）。参考 worktree-lifecycle.md 中对应流程的完整步骤。</agent_hint>
</task>
