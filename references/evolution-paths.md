# 进化路径详细定义

归档完成后按健康评分走四条路径。配置项 `evolution_mode` 控制（默认 `auto`，设为 `off` 跳过全部）。

## CAPTURE 路径（成功经验）

触发条件：`health-history.jsonl` 最近一条评分 ≥ 8.0

执行步骤：
1. 执行 `evolution_reflect.py --mode capture --specs-dir .specs/<id> --health-score <分>`
2. 成功策略存入 `.specs/evolution/strategies.jsonl`
3. 输出「🏆 策略已捕获：{approach}（评分 {score}）」

## FIX 路径（失败改进）

以下条件满足任一即触发：
1. 连续 3 个 Change 健康评分下降（读 `health-history.jsonl` 最近 3 条）
2. 同一归因标签在最近 5 个 Change 中出现 ≥3 次（读 `.specs/evolution/` 下的信号历史）
3. **首次进化**：`health-history.jsonl` 不存在或条目 < 3，且 `evolution_signal.py` 检测到 ≥1 个强信号 → 输出「🆕 首次进化：{信号摘要}」→ 直接执行 FIX 流程

执行步骤：
1. 输出「🧬 进化信号已触发：{原因}，正在运行进化分析」
2. 执行 `evolution_signal.py` → `evolution_reflect.py --mode reflect`
3. 展示假设和归因摘要
4. 有顿悟时 → 额外输出「💡 顿悟：{root_cause}（已出现 N 次）→ 建议：{advice}」，请用户确认是否写入 LESSONS.md

## BITTER PILL 路径（规则自审计）

归档后自动执行：
1. 运行 `python3 references/scripts/bitter_pill_audit.py --output .specs/<id>/BITTER-PILL.md`（`--skill-dir` 可选，默认自动发现）
2. 产出 KEEP / REVIEW / CANDIDATE 审计报告
3. CANDIDATE 项需用户逐条确认
4. 输出「💊 苦丸审计完成：KEEP N / REVIEW N / CANDIDATE N」

## SUGGEST 路径（改进建议）

触发条件：`.specs/evolution/skill-feedback.jsonl` 存在且含 `processed=false` 的条目

执行步骤：
1. 读取未处理的 skill 反馈，按频率排序
2. 运行 `evolution_reflect.py --mode suggest --feedback .specs/evolution/skill-feedback.jsonl --output .specs/evolution/<id>-suggestions.json`
3. 生成改进假设报告
4. 展示假设摘要，请用户逐条确认
5. 用户确认的改进 → 记录到建议列表，由用户手动执行修改
6. 全部处理完成后，将 skill-feedback.jsonl 中的对应条目标记为 `processed=true`

**安全原则**：SUGGEST 路径不自动修改 SKILL.md 或 references/ 下的任何文件。

**SUGGEST 不可自动执行的症状清单**（出现任一条即需用户逐条确认）：
1. 建议删除现有闸门检查或 HARD-GATE 机制
2. 建议修改角色红线的核心边界
3. 建议增加新的 Skill 链式调用白名单条目
4. 建议绕过 STATE.md 状态管理直接操作文件
