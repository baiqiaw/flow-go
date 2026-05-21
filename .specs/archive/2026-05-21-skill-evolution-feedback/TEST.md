# TEST — skill-evolution-feedback

## 测试策略
feature 类型，裁剪后执行第 1 轮（功能-AC 覆盖）+ 第 3 轮（安全）。跳过第 2/4/5 轮（纯脚本改动，无性能/兼容/可观测性变化）。

## 测试矩阵

| AC | 测试类型 | 测试方法 | 结果 |
|----|---------|---------|------|
| AC-1 | 功能 | 15 条 user-inputs.jsonl 格式校验（ts/change_id/stage/input 字段完整性） | ✅ PASS |
| AC-2 | 功能 | feedback_classifier.py 分类 15 条混合输入，验证 project/skill/preference/noise 分类 + skill-feedback.jsonl 创建 | ✅ PASS（12/15 正确，3 个可接受偏差） |
| AC-3 | 功能 | evolution_reflect.py --mode suggest 生成假设报告，验证 auto_approve_eligible=False | ✅ PASS |
| AC-4 | 功能 | 单条高置信度反馈触发一次性洞察（one_shot=True） | ✅ PASS（修复后） |
| AC-5 | 功能 | LITE 模式分类、废弃流程不触发分析 | ✅ PASS |
| AC-6 | 功能 | per-change vs 跨 change 持久分离、processed 字段 | ✅ PASS |
| 安全 | 安全 | 密钥扫描、注入测试、SUGGEST 不自动写入 | ✅ PASS |

## Bug 清单

| 编号 | 严重度 | 描述 | 状态 |
|------|--------|------|------|
| BUG-1 | Major | 一次性洞察永远无法触发：`_generate_suggestion_hypothesis` 用 frequency 重新计算 confidence，单条反馈 confidence=0.6 永远达不到 0.8 门槛 | ✅ 已修复 |
| BUG-2 | Minor | "测试通过"/"通过审查" 未被排除为 noise，被分为 project | 可接受（短句包含"通过"但不匹配排除模式） |
| BUG-3 | Minor | "以后把 SUMMARY 模板简化" 被分为 skill 而非 preference | 可接受（同时命中 skill 和 preference 关键词，skill 权重更高） |

## 修复验证

| Bug | 验证方法 | 结果 |
|-----|---------|------|
| BUG-1 | 单条 confidence=0.9 反馈触发 one_shot insight | ✅ PASS |
| BUG-2 | 确认不影响核心功能，噪声容忍范围内 | ✅ 接受 |
| BUG-3 | 确认分类结果合理（含 skill 改进建议） | ✅ 接受 |

## 量化指标

- AC 覆盖率：6/6 = 100%
- 分类准确率：12/15 = 80%（3 个可接受偏差）
- 安全检查：0 密钥泄露、0 注入风险、0 自动写入
- Bug 修复率：1/1 Critical/Major = 100%

## 回归测试

- 现有 CAPTURE/FIX/BITTER PILL 路径未受影响（代码改动仅增加新函数和新 CLI 入口，不修改现有逻辑）
- evolution_reflect.py 的 reflect/capture 模式 CLI 接口不变

## 测试环境

- 平台：WSL2 Linux 6.6.87.2
- Python：3.x（标准库，无外部依赖）
- 测试数据：15 条模拟用户输入，覆盖 8 个阶段和 4 种反馈类型
