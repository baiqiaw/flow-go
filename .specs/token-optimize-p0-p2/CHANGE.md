# CHANGE — token-optimize-p0-p2

## Why（为什么做）
- **痛点场景**：flow-go 8 阶段流程中，AI 每个阶段都输出冗长工件（REQUIREMENT.md、DESIGN.md、TASK.md 等），约 30% token 消耗在礼貌用语、铺垫、重复解释上。长会话中上下文压缩可能裁剪关键流程规则，导致 AI "忘记"阶段纪律。子代理返回的冗长输出直接注入主上下文，进一步消耗 token 预算。关键操作（部署、git push）无安全边界，压缩模式下可能因输出过于简略导致误操作。
- **当前障碍**：SKILL.md 仅一次性注入，无 Per-Turn 强化机制；无输出风格分层控制；无子代理输出压缩契约；无可量化 token 度量。
- **不做后果**：每次完整流程浪费 30-50% token 预算，长会话行为漂移导致返工，子代理输出膨胀导致上下文耗尽快照丢失。

## What（做什么）
基于 caveman 插件分析，对 flow-go 实施 P0-P2 优化：
- P0：输出 token 分层控制（SKILL.md 增加 normal/tight/caveman/ultra 模式）+ Auto-Clarity 安全边界
- P1：Per-Turn 强化机制（Claude Code Hook + Codex CLI 内联回退）+ 子代理输出压缩契约
- P2：参考文档压缩（可选）+ token 消耗追踪（扩展 trace_collector.py）

## 影响面
- 涉及模块：SKILL.md、references/stages/*.md、references/scripts/trace_collector.py、新增 hooks/、修改 references/terse-mode.md（已存在，含基础压缩规则，需扩展为分层模式）
- 数据库变更：否
- API 变更：否
- 依赖变更：否（Hook 使用 Node.js，已在环境中有）
- CONTEXT 需更新：否（本项目当前无 CONTEXT.md，本次变更不引入新术语）

## 范围排除（这次不做）
- Wenyan（文言文）中文 token 优化模式（实验性，团队接受度待验证）
- caveman-compress 工件文件自动压缩（需独立评估对 AI 理解的影响）
- benchmark 基准测试完整体系（只做最小化 token 追踪）
- 不支持 Hook 的平台（如 Cursor、Windsurf）的适配（仅保证 Claude Code + Codex CLI）

## 验收线
- P0-P2 全部 6 项优化实现且通过回归测试
- 现有 evals（11 个场景）全部通过，无行为回归
- Claude Code Hook 机制正常工作（SessionStart + UserPromptSubmit）
- Codex CLI 内联回退机制正常工作
- Auto-Clarity 在部署/不可逆操作场景触发

## 路径建议
完整，理由：涉及核心 SKILL.md 编排逻辑变更、新增 Hook 系统、修改多个 stage 定义文件、跨阶段行为变更，需要完整的 8 阶段流程验证。

## 验证假设
| # | 假设 | 证据级别 | 验证方式 | 验证阶段 | 推翻信号 |
|---|------|---------|---------|---------|---------|
| 1 | 分层输出模式确实能降低 token 消耗 | B - caveman 项目 benchmark 数据 | 对比优化前后完整流程 token 消耗 | 4-测试 | 压缩比 < 20% |
| 2 | Per-Turn 强化不会干扰 stage 定义的行为指令 | C - 基于 caveman hook 设计模式推断 | 运行完整 evals 套件确认无行为回归 | 4-测试 | 任意 eval 场景失败 |
| 3 | Codex CLI 内联回退能达到与 Hook 等效的效果 | C - 基于 prompt 注入原理推断 | Codex CLI 上运行 evals 场景 | 4-测试 | Codex 行为与 Claude Code 显著偏离 |

## 终止条件
| # | 条件 | 触发阶段 | 触发后动作 |
|---|------|---------|----------|
| 1 | 任一 eval 场景回归（之前通过现在失败） | 4-测试 | 回退到 3-开发，修复后重新测试 |
| 2 | Hook 机制导致 Claude Code 会话启动失败 | 3-开发 | 回退到 1-设计，重新设计 Hook 容错 |
| 3 | 分层模式导致关键阶段信息丢失（如设计决策被过度压缩） | 5-审查 | 重新评估，调整默认模式或阶段映射 |
