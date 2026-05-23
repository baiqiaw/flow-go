# DESIGN — 进化系统自优化

## 1. 架构图

```
[归档流程]
   │
   ├── 4.3 新增：自动提取 metrics → health_scorer（AC-2）
   ├── 4.5 轨迹采集（已有）
   ├── 4.6 进化信号检测（已有，升级模糊匹配 AC-3）
   ├── 4.6b 反馈分析（已有）
   ├── 7-9 归档移动+清理（已有）
   ├── 自动进化触发（已有，升级首次进化 AC-6）
   │   ├── CAPTURE → strategies.jsonl → 1-design/3-develop 消费（AC-4）
   │   ├── FIX（升级首次进化门槛 AC-6）
   │   ├── BITTER PILL（升级自动发现 AC-5）
   │   └── SUGGEST（不变）
   └── 自检清单（新增 3 项进化检查 AC-1）

[阶段完成时]
   └── 轻量会话内进化检查（AC-7）
```

## 2. 文件改动清单

| 文件 | 改动类型 | AC | 说明 |
|------|---------|-----|------|
| `references/stages/special-flows.md` | 修改 | AC-1, AC-2 | 归档步骤 4.3 + 自检清单 + 首次进化提示 |
| `references/scripts/evolution_signal.py` | 修改 | AC-3 | 提取器增加模糊匹配 fallback |
| `references/scripts/_path_utils.py` | 修改 | AC-5 | 新增 resolve_skill_dir_for_audit() |
| `references/scripts/bitter_pill_audit.py` | 修改 | AC-5 | --skill-dir 改为可选，默认自动发现 |
| `references/stages/1-design.md` | 修改 | AC-4 | 步骤 0 增加策略注入 |
| `SKILL.md` | 修改 | AC-6, AC-7 | 首次进化条件 + 轻量会话内进化 + BITTER PILL 调用方式 |
| `references/scripts/validate_skill.py` | 不改 | — | 验证脚本不做改动 |

## 3. 各 AC 实现方案

### AC-1：归档自检进化检查项
- 位置：`special-flows.md` 自检清单
- 新增 3 项检查（在现有 `轨迹已采集` 之后）
- 格式与现有自检项一致

### AC-2：健康评分自动计算
- 位置：`special-flows.md` 归档流程，步骤 4 和 4.5 之间新增步骤 4.3
- AI 从工件自动提取指标并构造 metrics JSON：
  - `ac_total/ac_passed`：从 TEST.md 的 AC 表统计
  - `test_rounds_completed/skipped`：从 TEST.md 统计
  - `review_rounds`：从 REVIEW.md 读取
  - `code_lines_added/removed`：从 SUMMARY.md 读取
  - `boundary_violations`：从 REVIEW.md 统计
  - `artifacts_complete`：扫描 .specs/<id>/ 下实际存在的工件
- 不改 health_scorer.py 本身（它已支持 stdin/文件输入）
- AI 执行：构造 metrics.json → `python3 health_scorer.py metrics.json`

### AC-3：信号检测模糊匹配
- 位置：`evolution_signal.py` 每个提取器函数
- 策略：精确匹配不变，新增 fallback 模糊正则
- 改动范围：
  - `_extract_review_rework()`：增加"返工/重做/评审未通过"
  - `_extract_test_repeated()`：增加"反复/多次出现/重复"
  - `_extract_gate_blocked()`：增加"前置条件/未通过检查/条件不满足"
  - `_extract_similar_error()`：增加"同类/类似/再次出现"
- 原则：精确匹配优先，模糊只在没有精确匹配时 fallback

### AC-4：CAPTURE 路径闭环
- 位置：`1-design.md` 步骤 0（新增）
- 3-develop.md 步骤 3 已有策略复用，不需要改
- 1-design.md 新增：检查 strategies.jsonl，取 score 最高的 3 条，输出参考
- 无策略文件时静默跳过

### AC-5：BITTER PILL 自动发现
- `_path_utils.py` 新增 `resolve_skill_dir_for_audit()`
  - 1. 从 `__file__` 推导（现有逻辑）
  - 2. 从项目根目录找 SKILL.md
  - 3. 从 `FLOWGO_SKILL_DIR` 环境变量
- `bitter_pill_audit.py` 改 `--skill-dir` 为可选参数，默认调自动发现
- `SKILL.md` 中 BITTER PILL 调用去掉 `<flow-go skill 目录>` 占位符

### AC-6：新项目首次进化
- 位置：`SKILL.md` 自动进化触发 + `special-flows.md`
- FIX 路径增加首次进化条件：
  - health-history.jsonl 不存在或条目 < 3
  - evolution_signal 检测到 ≥1 个强信号
  - 输出「🆕 首次进化」标记

### AC-7：轻量会话内进化
- 位置：`SKILL.md` 第七步状态更新
- 在"决策同步检查"之后新增"轻量进化检查"
- 从阶段工件中检测 user_correction 和 gate_blocked
- 纯文本输出，不写文件不调脚本

## 4. 风险清单

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| 模糊匹配误报信号 | 中 | 低 | 模糊匹配只在精确匹配无结果时 fallback |
| health_scorer AI 提取 metrics 不准确 | 中 | 低 | 评分本身是趋势指标，单次偏差可容忍 |
| strategies.jsonl 注入膨胀上下文 | 低 | 低 | 限制 3 条，每条截断到 200 字 |
| BITTER PILL 自动发现指向错误目录 | 低 | 中 | 保留 --skill-dir 覆盖，优先用户显式指定 |
