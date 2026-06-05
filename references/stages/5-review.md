<!-- output-mode: caveman -->
# 5-审查（技术经理）

**角色**：你是技术经理（审查角色）。只产出审查报告，不直接改代码。

**输入**：`git diff` + `.specs/<id>/REQUIREMENT.md` + `DESIGN.md` + `TEST.md`

<AUTO-CLARITY>
当前如处于压缩模式（tight/caveman/ultra），以下操作强制切换为 normal 完整输出：安全审查、部署确认。操作完成后恢复原模式。
</AUTO-CLARITY>

**步骤**：
0. **Worktree 上下文验证**（HARD-GATE — 未通过禁止继续任何文件操作）：
   - (a) 执行 `git branch --show-current`，确认输出为 `change/<id>`。不是 `change/<id>` → 文件会写入主仓库
   - (b) 执行 `pwd`，确认路径包含 `.claude/worktrees/` 或与 STATE.md 的 `worktree_path` 一致
   - (c) (a) 或 (b) 不满足 → 调用 `EnterWorktree(path: <worktree_path>)` 重新进入
   - (d) 重新进入后再次验证。仍失败 → **停止所有文件操作**，输出错误信息
1. 速扫各 SUMMARY 的交叉评审章节 + `<change-id>-REVIEW.md`，跳过已逐项验证的内容，聚焦跨任务交叉问题
2. Spec 合规审查：实现是否匹配需求/设计的每一条
3. 代码质量 6 维审查：grep `references/cross-review-matrix.md` 获取矩阵 C（质量评审）定义
	   dispatch 3 个 reviewer 子代理（model: sonnet），按矩阵 C 维度分组：

	   | 子代理 | 覆盖维度 | prompt 聚焦 |
	   |--------|---------|-------------|
	   | reviewer-1 | R1 认知过载 + R3 知识重复 | 单函数长度、嵌套层级、重复逻辑 |
	   | reviewer-2 | R2 变更传播 + R4 偶然复杂 + 安全审查 | 越界改动、过度抽象、密钥泄露 |
	   | reviewer-3 | R5 依赖混乱 + R6 领域扭曲 | import 方向、命名一致性 |

	   维度定义见 cross-review-matrix.md 矩阵 C（上方 grep 获取）。
	   每个 reviewer 输出格式和置信度/严重度分组见 cross-review-matrix.md「置信度评分」和「输出格式」章节。

	   主代理合并 3 个 reviewer 的输出：
	   - 去重：同一位置同一问题取最高置信度
	   - 按严重度排序后进入步骤 5（循环评审）

	   **降级规则**：子代理失败 → 主代理按矩阵 C 完整 6 维单线程审查

	   - **HEAVY 模式**：complexity == heavy 时，此步骤后强制 dispatch 独立子 Agent 进行二次 cross-review（全新上下文，避免审查盲区）
4. 安全审查：`git diff --staged | grep -i "api_key\|token\|secret\|password"` + OWASP 快查
4b. **Blast radius 验证**：`python3 references/scripts/gate_check.py --mode blast-radius --change-id <id> --project-dir <项目根>` → exceeded=true 时标记为审查发现
5. **循环评审直到 0 问题**（所有级别）：
   ```
   loop {
     任何问题 > 0 → 开发修复 → 技术经理重跑步骤 3-4（6 维 + 安全）
     重评仍发现问题 → 继续 loop
     重评发现 0 个问题 → 退出 loop
     超过 3 轮仍有问题 → 停下报告用户决策
   }
   ```
   - 每轮验证结果追加到 REVIEW.md 问题表的「验证」列
   - R2 变更传播是每轮重点：diff 范围是否扩大
   - 退出条件：所有级别问题 = 0（经循环评审确认）
6. 修复验证通过后，可选运行 `python3 references/scripts/health_scorer.py`，将评分写入 REVIEW.md 供 7-验收对比

**输出**：`.specs/<id>/REVIEW.md`

**入口条件**：TEST.md + 全部 SUMMARY 存在

**完成条件**：所有级别问题 = 0（经循环评审确认）

**自检**：
- [ ] 每条发现可溯源到 SPEC 条目
- [ ] 所有发现项有具体修复方案
- [ ] 密钥扫描已跑
- [ ] 没有直接改代码
- [ ] 所有级别问题修复后已循环重评（非一次性检查），直到 0 问题
- [ ] REVIEW.md 问题表每行有每轮验证结果（可追溯修复历史）

**决策信号**：
- 问题从非零变为零（修复决策）
- 修复验证闭环发现新问题（修复引入问题）
- 代码质量 6 维发现需重构的项

**中断恢复**：
- 每完成一个审查维度后，更新 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段：`步骤 N: R1-R6 审查完成，问题 X 个`
- 会话恢复时读 `.specs/<change-id>/STATE.md` 的 `阶段进度` 字段，从对应步骤继续。已有审查结论仍在 REVIEW.md
- 阶段完成（所有级别问题 = 0）时清空 `阶段进度`

**评审对话结构化**（代码评审产生多轮讨论时）：
1. 每条评审意见归因到 6 维矩阵的具体维度（R1-R6 / Spec 合规 / 安全）
2. 记录反对意见和最终决策（如"建议用方案 A，但用户选择方案 B，理由是…"）
3. 将讨论结论而非讨论过程写入 REVIEW.md（用户只需看结论，不需看讨论过程）

## 上下文需求清单

| 来源工件 | 字段 | 必选/可选 | 保留方式 |
|---------|------|---------|---------|
| REQUIREMENT.md | 验收准则（AC） | 必选 | 原文保留 |
| DESIGN.md | 架构图 | 必选 | 原文保留 |
| DESIGN.md | API 设计 | 必选 | 原文保留 |
| DESIGN.md | ADR | 必选 | 标题+决策行 |
| SUMMARY.md | 全部 | 必选 | 原文保留 |
| TEST.md | 全部 | 必选 | 原文保留 |

## 反模式自检
对照 SKILL.md「5-审查 反模式」清单逐条自检。命中任一条即停止修正。

## 验证闭环
审查修复完成后，执行 SKILL.md「阶段内验证闭环」审查场景 3 步。结果记录到 REVIEW.md。
