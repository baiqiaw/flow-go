# TASK — 进化系统自优化

## T01：_path_utils.py 增加 skill 目录自动发现
- **AC**：AC-5
- **改动文件**：`references/scripts/_path_utils.py`
- **内容**：新增 `resolve_skill_dir_for_audit()` 函数，3 级查找（脚本位置→项目根→环境变量）
- **verify**：`python3 -c "from references.scripts._path_utils import resolve_skill_dir_for_audit; print(resolve_skill_dir_for_audit())"` 输出包含 SKILL.md 的目录路径
- **write_files**：references/scripts/_path_utils.py

## T02：bitter_pill_audit.py --skill-dir 改为可选
- **AC**：AC-5
- **改动文件**：`references/scripts/bitter_pill_audit.py`
- **依赖**：T01
- **内容**：`--skill-dir` 从 required=True 改为 default=None，None 时调 resolve_skill_dir_for_audit()
- **verify**：`python3 references/scripts/bitter_pill_audit.py`（不带 --skill-dir）不报参数错误
- **write_files**：references/scripts/bitter_pill_audit.py

## T03：evolution_signal.py 信号检测模糊匹配
- **AC**：AC-3
- **改动文件**：`references/scripts/evolution_signal.py`
- **内容**：5 个提取器增加模糊匹配 fallback 正则
- **verify**：`python3 -c "from references.scripts.evolution_signal import detect; print('OK')"` 无报错
- **write_files**：references/scripts/evolution_signal.py

## T04：归档流程新增步骤 + 自检清单 + 首次进化
- **AC**：AC-1, AC-2, AC-6
- **改动文件**：`references/stages/special-flows.md`
- **内容**：
  1. 步骤 4.3：健康评分自动计算（AI 从工件提取 metrics → 调 health_scorer）
  2. 自检清单新增 3 项
  3. 步骤 4.6 首次进化检测提示
- **verify**：grep 确认包含 "4.3" "健康评分" "首次进化" 关键字
- **write_files**：references/stages/special-flows.md

## T05：1-design.md 策略注入
- **AC**：AC-4
- **改动文件**：`references/stages/1-design.md`
- **内容**：在步骤 1 前新增步骤 0：读取 strategies.jsonl 注入成功策略
- **verify**：grep 确认包含 "strategies.jsonl" 关键字
- **write_files**：references/stages/1-design.md

## T06：SKILL.md 进化触发逻辑更新
- **AC**：AC-5, AC-6, AC-7
- **改动文件**：`SKILL.md`
- **依赖**：T02（BITTER PILL 调用方式）
- **内容**：
  1. BITTER PILL 调用去掉 `<flow-go skill 目录>` 占位符
  2. FIX 路径增加首次进化条件
  3. 状态更新新增轻量会话内进化检查
- **verify**：grep 确认包含 "首次进化" 和 "轻量进化检查" 关键字
- **write_files**：SKILL.md

## 执行顺序
T01 → T02 → T03（并行可行，但 T02 依赖 T01）
T04, T05, T06 可并行（互不依赖）
