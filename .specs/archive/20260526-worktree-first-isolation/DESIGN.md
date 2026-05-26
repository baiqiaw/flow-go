# DESIGN — worktree-first-isolation

> change-id: `worktree-first-isolation`
> 复杂度: STANDARD
> 路径: 增量

## 问题陈述

flow-go 的 change 在主仓库共享工作目录，导致并行 change 交叉污染、STATE.md 索引表与实际目录脱节、归档残留。需要将 worktree 创建前移到 change-id 生成时，用 git 物理隔离替代手动同步。

## 技术选型

| 选项 | 方案 | 选择 | 理由 |
|------|------|------|------|
| 活跃 change 发现机制 | A: git worktree list / B: STATE.md 索引表 + 校验 / C: 两者并存 | A | B 是当前方案（已证明会脱节），C 增加维护成本且保留了脱节根因 |

证据级别：B（已在项目中使用 git worktree，行为可验证）

## 架构图

### 当前架构（问题）

```
主仓库 main/
├── STATE.md          ← 手动维护索引表（可能脱节）
├── .specs/
│   ├── change-A/     ← 与 change-B 共享目录
│   ├── change-B/     ← commit 可能交叉污染
│   └── archive/
└── (所有 change 在同一个工作树中工作)
```

### 目标架构（worktree-first）

```
主仓库 main/
├── STATE.md          ← 仅 Pipeline 待续 + 更新时间（无索引表）
├── .specs/
│   └── archive/      ← 只有归档后的目录

worktree change/A/           worktree change/B/
├── .specs/A/                ├── .specs/B/
│   ├── STATE.md             │   ├── STATE.md
│   ├── REQUIREMENT.md       │   ├── REQUIREMENT.md
│   └── ...                  │   └── ...
└── (物理隔离)               └── (物理隔离)
```

### 启动发现流程

```
flow-go 启动
    │
    ├─ git worktree list
    │   │
    │   ├─ 无 change/* worktree → 主仓库干净
    │   │   ├─ 用户描述新需求 → 创建 worktree → 0-需求
    │   │   └─ 用户说"继续" → 无活跃 change，提示
    │   │
    │   ├─ 1 个 change/* worktree
    │   │   └─ 自动进入 → 读 .specs/<id>/STATE.md → 路由到当前阶段
    │   │
    │   └─ N 个 change/* worktree
    │       └─ 列出选项 → 用户选择 → 进入对应 worktree
```

### 归档流程（拆分）

```
┌─────────────────────────────────┐
│ worktree change/<id>/           │
│                                 │
│ 1. SUMMARY 提名                 │
│ 2. PROGRESS 清理                │
│ 3. 目录移动到 .specs/archive/   │
│ 4. git commit（归档提交）        │
│ 5. ExitWorktree                 │
└────────────┬────────────────────┘
             │ merge to main
             ▼
┌─────────────────────────────────┐
│ 主仓库 main/                    │
│                                 │
│ 6. 合并归档分支                  │
│ 7. 全局文件追加                  │
│    - ARCHIVE-INDEX.md           │
│    - health-history.jsonl        │
│    - traces.jsonl                │
│ 8. git commit（全局更新）        │
│ 9. 清理 worktree 分支            │
└─────────────────────────────────┘
```

## 改动设计

### 改动 1: SKILL.md 第一步重写

**当前逻辑（行号 79-95）**：读 STATE.md → 解析索引表 → 活跃数 0/1/>N 分支
**改为**：

```markdown
1. 尝试读项目根目录 `STATE.md`。不存在 → 新项目，跳过
2. **活跃 change 发现**：执行 `git worktree list --porcelain`，过滤行以 `branch refs/heads/change/` 开头的条目，提取 worktree 路径和 change-id
3. **一致性校验**：调用 `validate_state.py`（新版，不含索引表校验）
4. 校验通过后解析活跃 change：
   - **0 个 worktree**：无活跃 change
   - **1 个 worktree**：自动读该 worktree 的 `.specs/<id>/STATE.md` → 路由
   - **>1 个 worktree**：用 AskUserQuestion 让用户选择
5. 选定 change 后检查：`中断任务` 非空 → 走回溯流程
6. Worktree 检查：直接使用当前 worktree 路径
7. 读 `.specs/CONTEXT.md`（如存在）
8. `Pipeline 待续` 非空且无活跃 worktree → pipeline 衔接
```

**删除的旧逻辑**：
- 步骤 2 旧格式检测与迁移（L79-84）
- 步骤 4 索引表解析 + 活跃数分支（L86-89）

**横切关注点同步**（SKILL.md L60-68 前置动作）：
- `change_id` 获取来源从"STATE.md 活跃 Change 索引表读取"改为"当前 worktree 路径推导（路径中 `change/<id>` 的 `<id>` 部分）"
- `stage` 获取来源不变（仍从 `.specs/<id>/STATE.md` 读取）
- "STATE.md 有活跃 Change（索引表非空）"判断改为"当前在 change/* worktree 中"

### 改动 2: SKILL.md 第七步状态更新简化

**当前**（L355-360）：更新 STATE.md 索引表 + 启动新 change 添加索引行 + 归档移除索引行
**改为**：
- 启动新 change：创建 worktree（不需要更新索引表）
- 阶段转换：只更新 per-change STATE.md（不更新根 STATE.md）
- 归档：worktree 清理（不需要从索引表移除行）

### 改动 3: 0-requirement.md 新增 worktree 创建步骤

在步骤 3（生成 change-id）后新增步骤 3.5：

```markdown
3.5 **Worktree 创建**：
   - (a) 调用 EnterWorktree（name: <change-id>），创建分支 `change/<id>`
   - (b) 进入 worktree 后，创建 `.specs/<id>/` 目录
   - (c) 将之前生成的 REQUIREMENT.md 和 CHANGE.md 写入 `.specs/<id>/`
   - (d) 创建 `.specs/<id>/STATE.md`，`worktree_path` 写入实际路径
   - (e) EnterWorktree 不可用 → 回退到 Bash：`git worktree add .claude/worktrees/<id> -b change/<id>` + `cd .claude/worktrees/<id>`（必须切换 cwd，后续路径操作才能指向 worktree）
```

### 改动 4: 2-task.md 移除步骤 0

删除 2-task.md 步骤 0（worktree 创建），因为已在 0-需求阶段完成。保留 worktree 验证（确认 `worktree_path` 非空且目录存在）。

### 改动 5: special-flows.md 归档流程拆分

**归档步骤重排**：

```
worktree 内执行（步骤 1-7）：
1. SUMMARY 提名
2. PROGRESS 清理
3. 目录移动到 .specs/archive/（archive-move.md）
4. 验证移动成功
5. git commit（仅含归档目录移动）
6. ExitWorktree（action: keep）
7. 回到主仓库

main 中执行（步骤 8-12）：
8. merge worktree 分支到 main：`git merge change/<id> --no-ff`
9. 全局文件追加：ARCHIVE-INDEX.md + health-history.jsonl + traces.jsonl
10. git commit（全局更新）
11. 清理 worktree 分支：`git worktree remove .claude/worktrees/<id>` + `git branch -d change/<id>`
12. git push + clean 验证
```

**新增 commit 前断言**（步骤 5 前）：
```bash
test ! -d .specs/<id> || { echo "❌ 归档断言失败：原目录仍存在"; exit 1; }
```

#### 非 归档特殊流程的索引表操作映射

special-flows.md 中除归档外还有 5 个流程引用了索引表，需统一替换：

| 流程 | 旧操作（索引表） | 新操作（worktree） |
|------|----------------|-------------------|
| 热修 L11 | 取 STATE.md 索引表的活跃 Change | `git worktree list` 获取当前 worktree（热修在活跃 change 的 worktree 中执行） |
| 中断 L157 | 取 STATE.md 索引表的活跃 Change（必须非空） | `git worktree list` 确认活跃 worktree 存在 |
| 中断 L160 | STATE.md 索引表移除该 change 行 | 保留 worktree 不清理（中断后可恢复） |
| 并行 L195 | STATE.md 索引表新增新 change 行 | 为新 change 创建新 worktree |
| 废弃 L230 | 从索引表移除该 change 行 | 清理 worktree（ExitWorktree action: remove） |
| 回溯 L258 | 读 STATE.md 索引表（活跃 Change） | `git worktree list` 找到目标 worktree 并进入 |

### 改动 6: validate_state.py 重写

**删除**：
- `PROJECT_REQUIRED_FIELDS` 中的索引表字段
- `parse_change_ids_from_index()` 函数
- `detect_legacy_format()` 函数
- 索引表解析和一致性校验逻辑

**新增**：
- `discover_active_changes()` 函数：调用 `git worktree list --porcelain`，解析 `change/*` 分支
- worktree 存在性校验：验证 worktree 路径存在且 `.specs/<id>/STATE.md` 可读

**保留**：
- `validate_change_state()`：per-change STATE.md 校验不变
- 向后兼容：旧归档目录的 STATE.md 仍可读取（不报错）

### 改动 7: meta-artifacts.md STATE.md 模板更新

**当前模板**（含索引表）：
```markdown
## 活跃 Change
| change-id | 阶段 | 最后更新 |
```

**新模板**：
```markdown
## 活跃 Change
（由 git worktree list 管理）
```

### 改动 8: commit message 规范

special-flows.md 中增加非归档 commit 的 change-id 关联规范。所有阶段内的 commit 消息格式：
```
<type>(<scope>)(<change-id>): <description>
```

## 备选方案

| 被排除方案 | 排除理由 |
|-----------|---------|
| 保留索引表 + 定期校验 | 保留根因（手动同步），只加补丁 |
| worktree 中也更新全局文件 | 并行 worktree 全局文件 merge 冲突风险 |
| 完全不使用 STATE.md | Pipeline 待续等全局状态仍需文件持久化 |

## 风险清单

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| `git worktree list` 输出格式跨平台不一致 | 低 | 高 | 3-开发阶段在 WSL2 实测验证 |
| 全局文件 merge 冲突 | 中 | 中 | 全局文件仅在 main 中追加，不在 worktree 中修改 |
| worktree 创建失败（磁盘空间/权限） | 低 | 中 | EnterWorktree 有错误处理，回退到提示用户 |
| 旧测试用例（test_stage_mismatch 等）需要重写 | 高 | 低 | 4 个测试用例直接重写 |

## 既有架构对齐

**触碰模块**：
- SKILL.md（第一步、第三步、第七步）
- references/stages/0-requirement.md（步骤 3.5）
- references/stages/2-task.md（步骤 0 移除）
- references/stages/special-flows.md（归档/废弃/回溯/中断/并行流程）
- references/scripts/validate_state.py（重写）
- references/artifacts/meta-artifacts.md（模板更新）
- references/common/pipeline-continuation.md（索引表引用清理）

**禁动清单**：
- gate_check.py：不修改（仅读 per-change STATE.md）
- health_scorer.py：不修改（仅调整调用位置）
- evolution_signal.py：不修改
- gate_l1/l2/l3.py：不修改

**沿用决策**：
- per-change STATE.md 格式不变
- archive-move.md 硬闸门验证不变
- cross-review-matrix.md 不变
- worktree-lifecycle.md 大部分保留，仅更新创建时机描述

## 文件变更清单

| 文件 | 变更类型 | 改动量 |
|------|---------|--------|
| `SKILL.md` | 修改（第一步重写、第三步 worktree 逻辑、第七步简化） | ~60 行 |
| `references/stages/0-requirement.md` | 修改（新增步骤 3.5） | ~10 行 |
| `references/stages/2-task.md` | 修改（移除步骤 0，简化为验证） | -10 行 |
| `references/stages/special-flows.md` | 修改（归档拆分、6 个流程索引表引用清理、commit 断言） | ~80 行 |
| `references/scripts/validate_state.py` | 重写 | ~100 行 |
| `references/artifacts/meta-artifacts.md` | 修改（模板简化） | ~20 行 |
| `references/common/pipeline-continuation.md` | 修改（索引表引用清理） | ~5 行 |
| `tests/test_scripts.py` | 修改（重写 TestValidateState 用例） | ~30 行 |

总改动量：~295 行（新增 + 修改 + 删除）

## 自检

- [x] ADR 有替代方案对比（技术选型表 + 备选方案章节）
- [x] 有风险项 + 缓解（4 条风险）
- [x] 棕地项目有对齐检查（触碰模块 + 禁动清单 + 沿用决策）
- [x] 无直接实现代码
- [x] 备选方案章节已填写
