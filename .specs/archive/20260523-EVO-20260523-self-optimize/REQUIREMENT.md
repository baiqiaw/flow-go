# REQUIREMENT — 进化系统自优化

## 背景
flow-go 有 4 条进化路径（CAPTURE/FIX/BITTER PILL/SUGGEST）和 5 个辅助机制（signal/reflect/gate/trace/flywheel），设计精巧但在其他项目中从未触发过。根本原因：
1. 所有进化路径锁死在归档流程，新项目前 3 个 change 达不到门槛
2. health_scorer 需手动构造 metrics JSON，AI 经常跳过
3. 信号检测依赖精确中文正则，不同项目工件格式不统一
4. BITTER PILL 需要 skill 目录路径，跨项目不透明
5. CAPTURE 产出 strategies.jsonl 但无消费方，开环不闭环
6. 归档自检缺少进化相关检查项

## 验收标准（AC）

### AC-1：归档自检包含进化检查项
- 归档自检清单新增 3 项：健康评分已计算、进化信号已检测、自动进化已执行
- 不通过时归档流程不继续（与现有闸门机制一致）

### AC-2：健康评分自动计算
- 归档流程中新增步骤，从工件自动提取 metrics 并调用 health_scorer
- 提取逻辑覆盖：AC 通过率、测试轮次、评审轮次、代码行数、边界违反、工件完整度
- 无需 AI 手动构造 JSON

### AC-3：信号检测模糊匹配
- evolution_signal.py 的 10 个提取器增加模糊匹配模式
- 对"交叉评审"增加"返工/重做/评审未通过"等近义词
- 对"闸门阻断"增加"前置条件不满足/未通过检查"等近义词
- 保持现有精确匹配优先，模糊匹配作为 fallback

### AC-4：CAPTURE 路径闭环
- 1-设计 和 3-开发 阶段开头读取 strategies.jsonl 注入历史成功策略
- 无策略文件时静默跳过，不输出任何内容
- 注入策略限制为评分最高的 3 条，避免上下文膨胀

### AC-5：BITTER PILL 自动发现 skill 目录
- _path_utils.py 新增 resolve_skill_dir_for_audit() 函数
- 支持从脚本位置、项目根目录、环境变量 3 种方式发现
- BITTER PILL 调用改用此函数，SKILL.md 中不再需要 `<flow-go skill 目录>` 占位符

### AC-6：新项目首次进化
- health-history.jsonl 条目 < 3 时，FIX 路径降级为"有 1 个强信号即触发"
- 输出「🆕 首次进化」标记，区分常规 FIX 和首次进化
- BITTER PILL 首次运行使用宽松阈值

### AC-7：轻量会话内进化
- 每个阶段完成时（不依赖归档），检查 user_correction 和 gate_blocked 信号
- 有信号 → 即时输出建议，不写文件不调脚本
- 输出格式：「⚡ 即时信号：{类型} → 建议：{advice}」

## 非目标
- 不修改进化系统的整体架构（4 路径 + 5 辅助的结构保持不变）
- 不添加新的进化路径
- SUGGEST 路径保持"不自动修改"的安全原则

## 约束
- 所有 Python 脚本改动保持向后兼容（现有调用方式不受影响）
- 不引入新的外部依赖
- SKILL.md 行数增长不超过 30 行
